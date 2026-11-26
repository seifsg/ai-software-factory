//! A child process and everything it starts, killable as one: a Job Object on Windows, a process group elsewhere.
//! Why: `taskkill /T` walks the tree once, so a process started while it runs survives (1 in 5 runs under load
//! left a grandchild alive). Every process created inside a job belongs to it, so terminating the job misses none.

use std::process::{Child, Command, Stdio};

/// The spawned child with its kill handle.
pub struct Tree {
    pub child: Child,
    #[cfg(windows)]
    job: Option<win::Job>,
}

impl Tree {
    pub fn spawn(mut command: Command) -> std::io::Result<Self> {
        #[cfg(unix)]
        std::os::unix::process::CommandExt::process_group(&mut command, 0);
        // The host's own stdout and stderr stay out of the tree: an orphan holding them would hang a host call waiting for their end.
        #[cfg(windows)]
        let _private = crate::streams::PrivateStreams::new()?;
        let child = command.spawn()?;
        #[cfg(windows)]
        let job = win::Job::holding(&child);
        Ok(Self {
            child,
            #[cfg(windows)]
            job,
        })
    }

    /// After the child exited: kills what it left running (a browser the agent never closed). Windows only: the job is
    /// this run's own, so it can never name a stranger; a Unix group id may be reused once its leader is reaped.
    pub fn reap(&self) {
        #[cfg(windows)]
        if let Some(job) = &self.job {
            job.terminate();
        }
    }

    /// Kills the child and all it started, then reaps it. Only for a running child: after it exited its pid may be
    /// reused by an unrelated process.
    pub fn kill(&mut self) {
        #[cfg(windows)]
        let killed = self.job.as_ref().is_some_and(win::Job::terminate);
        #[cfg(not(windows))]
        let killed = false;
        if !killed {
            fallback(self.child.id());
        }
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

/// `taskkill /T` where no job could be made (a host that forbids nesting), `kill -KILL -<group>` on Unix.
fn fallback(pid: u32) {
    let mut k = if cfg!(windows) {
        let mut k = crate::paths::quiet_command("taskkill");
        k.args(["/PID", &pid.to_string(), "/T", "/F"]);
        k
    } else {
        let mut k = crate::paths::quiet_command("kill");
        k.args(["-KILL", &format!("-{pid}")]);
        k
    };
    let _ = k.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null()).status();
}

#[cfg(windows)]
mod win {
    use std::ffi::c_void;
    use std::os::windows::io::AsRawHandle;
    use std::process::Child;

    #[link(name = "kernel32")]
    unsafe extern "system" {
        fn CreateJobObjectW(attributes: *mut c_void, name: *const u16) -> *mut c_void;
        fn AssignProcessToJobObject(job: *mut c_void, process: *mut c_void) -> i32;
        fn TerminateJobObject(job: *mut c_void, exit_code: u32) -> i32;
        fn CloseHandle(handle: *mut c_void) -> i32;
    }

    /// An anonymous job holding one child; its later descendants join it on creation.
    pub struct Job(*mut c_void);

    impl Job {
        /// `None` when the job cannot be made or the child cannot join it; the caller falls back to `taskkill`.
        pub fn holding(child: &Child) -> Option<Self> {
            // Plain kernel32 calls on a handle this process owns; null attributes and name make an unnamed job.
            let job = unsafe { CreateJobObjectW(std::ptr::null_mut(), std::ptr::null()) };
            if job.is_null() {
                return None;
            }
            let job = Self(job);
            (unsafe { AssignProcessToJobObject(job.0, child.as_raw_handle()) } != 0).then_some(job)
        }

        pub fn terminate(&self) -> bool {
            unsafe { TerminateJobObject(self.0, 1) != 0 }
        }
    }

    impl Drop for Job {
        fn drop(&mut self) {
            // No kill-on-close flag: closing the handle leaves a finished run's processes alone.
            unsafe { CloseHandle(self.0) };
        }
    }
}
