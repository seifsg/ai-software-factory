//! Machine-wide state every factory session on this PC shares: one user folder, process liveness and a
//! crash-safe lock file. Why: `queue` and `reserve` coordinate separate processes with no server and no
//! model tokens, and a crashed holder must never block the machine.

use crate::paths::{norm, text};
use std::fs;
use std::io::ErrorKind;
use std::path::{Path, PathBuf};
use std::time::Duration;

/// `<root>/<kind>`, created: root is `FACTORY_QUEUE_DIR` when set, else the user cache folder +
/// `ai-software-factory` (`LOCALAPPDATA` on Windows, the same for every shell; elsewhere `XDG_CACHE_HOME`,
/// else `$HOME/.cache`).
pub fn dir(kind: &str) -> Result<PathBuf, String> {
    let var = |k| std::env::var_os(k).filter(|v| !v.is_empty()).map(|v| PathBuf::from(norm(&v.to_string_lossy())));
    let root = match var("FACTORY_QUEUE_DIR") {
        Some(d) => d,
        None if cfg!(windows) => var("LOCALAPPDATA").ok_or("no LOCALAPPDATA: set FACTORY_QUEUE_DIR")?.join("ai-software-factory"),
        None => var("XDG_CACHE_HOME")
            .or_else(|| var("HOME").map(|h| h.join(".cache")))
            .ok_or("no XDG_CACHE_HOME or HOME: set FACTORY_QUEUE_DIR")?
            .join("ai-software-factory"),
    };
    if !root.is_absolute() {
        return Err(format!("machine folder {} is not absolute: sessions in other folders would not share it", text(&root)));
    }
    let d = root.join(kind);
    fs::create_dir_all(&d).map_err(|e| format!("cannot create {}: {e}", text(&d)))?;
    Ok(d)
}

/// A process by pid and, where the OS gives one, its start time, written `pid` or `pid-start`. Why: Windows
/// and Linux reuse pids, so a pid alone can name a stranger that keeps a dead owner's entry alive forever.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Owner {
    pub pid: u32,
    pub start: Option<u64>,
}

impl Owner {
    /// This process.
    pub fn me() -> Owner {
        let pid = std::process::id();
        Owner { pid, start: probe(pid).flatten() }
    }

    /// `pid` or `pid-start`; None for anything else. An old entry without a start time stays pid-only.
    pub fn parse(s: &str) -> Option<Owner> {
        let (pid, start) = match s.split_once('-') {
            Some((p, t)) => (p, Some(t.parse().ok()?)),
            None => (s, None),
        };
        Some(Owner { pid: pid.parse().ok()?, start })
    }

    /// True while this owner runs: its pid runs and, when both start times are known, they match.
    pub fn alive(self) -> bool {
        probe(self.pid).is_some_and(|now| self.start.zip(now).is_none_or(|(a, b)| a == b))
    }
}

impl std::fmt::Display for Owner {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self.start {
            Some(t) => write!(f, "{}-{t}", self.pid),
            None => write!(f, "{}", self.pid),
        }
    }
}

/// None when process `pid` is not running, else its start time when readable. A process of another user that
/// refuses the query still counts as running, start unknown.
#[cfg(windows)]
fn probe(pid: u32) -> Option<Option<u64>> {
    use std::ffi::c_void;
    #[link(name = "kernel32")]
    unsafe extern "system" {
        fn OpenProcess(access: u32, inherit: i32, pid: u32) -> *mut c_void;
        fn GetExitCodeProcess(process: *mut c_void, code: *mut u32) -> i32;
        fn GetProcessTimes(process: *mut c_void, created: *mut u64, exited: *mut u64, kernel: *mut u64, user: *mut u64) -> i32;
        fn CloseHandle(handle: *mut c_void) -> i32;
    }
    // PROCESS_QUERY_LIMITED_INFORMATION: the least access that reads an exit code and the process times.
    let h = unsafe { OpenProcess(0x1000, 0, pid) };
    if h.is_null() {
        return (std::io::Error::last_os_error().raw_os_error() == Some(5)).then_some(None); // ERROR_ACCESS_DENIED
    }
    // A FILETIME is two little-endian u32 halves, so a u64 reads it whole. The handle is closed once, below.
    let (mut code, mut t) = (0, [0u64; 4]);
    let running = unsafe { GetExitCodeProcess(h, &mut code) } != 0 && code == 259; // STILL_ACTIVE
    let timed = unsafe { GetProcessTimes(h, &mut t[0], &mut t[1], &mut t[2], &mut t[3]) } != 0;
    unsafe { CloseHandle(h) };
    running.then_some(timed.then_some(t[0]))
}

/// None when process `pid` is not running, else its start time when readable. A process of another user
/// (EPERM) still counts as running.
#[cfg(unix)]
fn probe(pid: u32) -> Option<Option<u64>> {
    unsafe extern "C" {
        fn kill(pid: i32, sig: i32) -> i32;
    }
    // Signal 0 only checks; pid 0 or past i32 would address a process group, never one process.
    let p = i32::try_from(pid).ok().filter(|p| *p > 0)?;
    (unsafe { kill(p, 0) } == 0 || std::io::Error::last_os_error().raw_os_error() == Some(1)).then(|| started(pid))
}

/// Field 22 (starttime) of `/proc/<pid>/stat`, counted after the parenthesised name, which may hold spaces.
#[cfg(target_os = "linux")]
fn started(pid: u32) -> Option<u64> {
    let stat = fs::read_to_string(format!("/proc/{pid}/stat")).ok()?;
    stat[stat.rfind(')')? + 1..].split_whitespace().nth(19)?.parse().ok()
}

// Other Unix has no portable start time, so liveness there is pid-only.
#[cfg(all(unix, not(target_os = "linux")))]
fn started(_: u32) -> Option<u64> {
    None
}

/// A machine-wide mutex: the file at its path holds its `Owner` and is removed on drop. A lock whose
/// owner died or whose pid now names another process is moved aside and taken, so a crash never blocks the machine.
pub struct Lock(PathBuf);

impl Lock {
    /// Takes the lock at `path`, checking every 50 ms while a live process holds it.
    pub fn take(path: PathBuf) -> Result<Lock, String> {
        let me = std::process::id().to_string();
        let mine = suffixed(&path, &format!("~{me}"));
        fs::write(&mine, Owner::me().to_string()).map_err(|e| format!("cannot write {}: {e}", text(&mine)))?;
        // A hard link publishes the file whole: no reader ever sees a lock without its owner.
        let taken = loop {
            match fs::hard_link(&mine, &path) {
                Ok(()) => break Ok(Lock(path)),
                Err(e) if e.kind() == ErrorKind::AlreadyExists => match clear_dead(&path, &me) {
                    Ok(true) => {}
                    Ok(false) => std::thread::sleep(Duration::from_millis(50)),
                    Err(e) => break Err(e),
                },
                Err(e) => break Err(format!("cannot lock {}: {e}", text(&path))),
            }
        };
        let _ = fs::remove_file(&mine); // only a leftover temp file when this fails; the lock is unaffected
        taken
    }
}

impl Drop for Lock {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}

/// Clears the lock at `path` when its owner is dead: true when it is gone, false while a live owner holds it.
/// Known gap: a third waiter can lock between a clearer's move-aside and its link-back of a live lock.
fn clear_dead(path: &Path, me: &str) -> Result<bool, String> {
    let holder = match fs::read_to_string(path) {
        Ok(t) => t,
        Err(e) if e.kind() == ErrorKind::NotFound => return Ok(true),
        Err(e) => return Err(format!("cannot read {}: {e}", text(path))),
    };
    let owner = Owner::parse(&holder).ok_or_else(|| format!("{} holds {holder:?}, not a pid: remove it by hand", text(path)))?;
    if owner.alive() {
        return Ok(false);
    }
    // Move it aside, then check what moved: another waiter may have cleared it and locked since the read.
    let tomb = suffixed(path, &format!("~tomb{me}"));
    match fs::rename(path, &tomb) {
        Ok(()) => {}
        Err(e) if e.kind() == ErrorKind::NotFound => return Ok(true),
        Err(e) => return Err(format!("cannot clear {}: {e}", text(path))),
    }
    let moved = fs::read_to_string(&tomb).map_err(|e| format!("cannot read {}: {e}", text(&tomb)))?;
    if moved != holder {
        fs::hard_link(&tomb, path).map_err(|e| format!("lock {} changed hands while clearing a dead owner: {e}", text(path)))?;
    }
    fs::remove_file(&tomb).map_err(|e| format!("cannot remove {}: {e}", text(&tomb)))?;
    Ok(true)
}

/// `path` with `tail` appended to its last component.
fn suffixed(path: &Path, tail: &str) -> PathBuf {
    let mut s = path.as_os_str().to_owned();
    s.push(tail);
    s.into()
}

/// `--flag value` pairs, each flag one of `names` and given at most once; None on anything else.
pub fn flags<'a, const N: usize>(args: &[&'a str], names: [&str; N]) -> Option<[Option<&'a str>; N]> {
    let mut out = [None; N];
    for pair in args.chunks(2) {
        let [flag, value] = pair else { return None };
        out[names.iter().position(|n| n == flag)?].replace(*value).is_none().then_some(())?;
    }
    Some(out)
}

/// An option's number in `lo..=hi`, `default` when the option is absent; None when out of range or no number.
pub fn number(value: Option<&str>, default: u64, lo: u64, hi: u64) -> Option<u64> {
    value.map_or(Some(default), |v| v.parse().ok()).filter(|n| (lo..=hi).contains(n))
}

/// True for 1..=`max` bytes, each ASCII alphanumeric or one of `extra`.
pub fn valid(name: &str, max: usize, extra: &str) -> bool {
    (1..=max).contains(&name.len()) && name.bytes().all(|b| b.is_ascii_alphanumeric() || extra.as_bytes().contains(&b))
}
