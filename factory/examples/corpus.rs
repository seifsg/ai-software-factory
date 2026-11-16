//! Dev-only corpus builder for the parity harness: copies a recorded run's session transcript and subagent
//! transcripts, stripped to what the guard reads (sidechain marks, posted step headings, delegate roles,
//! verdicts, CRITICAL marks), so no private text is kept. Line counts and file order survive.
//! `cargo run --example corpus -- <projects dir> <session id> <out dir>`; writes `<out>/<session>.jsonl`,
//! `<out>/<session>/subagents/agent-*.jsonl` and `<out>/order` (subagent files, oldest first).

use std::path::Path;

fn main() {
    let a: Vec<String> = std::env::args().skip(1).collect();
    let [projects, sid, out] = a.as_slice() else {
        eprintln!("usage: corpus <projects dir> <session id> <out dir>");
        std::process::exit(2);
    };
    let proj = std::fs::read_dir(projects)
        .expect("projects")
        .flatten()
        .map(|e| e.path())
        .find(|p| p.join(format!("{sid}.jsonl")).is_file())
        .expect("session transcript");
    let subs_out = Path::new(out).join(sid).join("subagents");
    std::fs::create_dir_all(&subs_out).expect("mkdir");
    let main = std::fs::read(proj.join(format!("{sid}.jsonl"))).expect("read session");
    std::fs::write(Path::new(out).join(format!("{sid}.jsonl")), strip(&main, session_line)).expect("write session");
    let mut subs: Vec<(u128, String)> = std::fs::read_dir(proj.join(sid).join("subagents"))
        .map(|rd| {
            rd.flatten()
                .filter(|e| e.file_name().to_string_lossy().starts_with("agent-") && e.file_name().to_string_lossy().ends_with(".jsonl"))
                .map(|e| (factory::paths::mtime_ns(&e.path()).unwrap_or(0), e.file_name().to_string_lossy().into_owned()))
                .collect()
        })
        .unwrap_or_default();
    subs.sort();
    for (_, name) in &subs {
        let data = std::fs::read(proj.join(sid).join("subagents").join(name)).expect("read sub");
        let mut first = true;
        let stripped = strip(&data, |l| {
            let r = sub_line(l, first);
            first = false;
            r
        });
        std::fs::write(subs_out.join(name), stripped).expect("write sub");
    }
    let order: String = subs.iter().map(|(_, n)| format!("{n}\n")).collect();
    std::fs::write(Path::new(out).join("order"), order).expect("write order");
    println!("{} subagent files", subs.len());
}

fn strip(data: &[u8], mut f: impl FnMut(&[u8]) -> String) -> String {
    let text = data.strip_suffix(b"\n").unwrap_or(data);
    text.split(|&b| b == b'\n').map(|l| f(l) + "\n").collect()
}

fn has(l: &[u8], p: &str) -> bool {
    memchr::memmem::find(l, p.as_bytes()).is_some()
}

/// A session line keeps its sidechain mark and the step headings its assistant text opened.
fn session_line(l: &[u8]) -> String {
    let mut s = factory::evidence::scan::Session::default();
    s.line(l);
    let side = if has(l, "\"isSidechain\"") { "\"isSidechain\":false," } else { "" };
    if !has(l, "\"role\":\"assistant\"") {
        return format!("{{{}}}", side.trim_end_matches(','));
    }
    let items: Vec<String> = s.sent.iter().map(|h| format!("{{\"type\":\"text\",\"text\":\"## {h} x\"}}")).collect();
    format!("{{{side}\"message\":{{\"role\":\"assistant\",\"content\":[{}]}}}}", items.join(","))
}

/// A subagent line: the brief's role on line 1; later, its own verdict and CRITICAL mark.
fn sub_line(l: &[u8], first: bool) -> String {
    if first {
        let mut s = factory::evidence::scan::Sub::default();
        s.line(l);
        return match s.role {
            Some('R') => "{\"message\":\"Role: reviewer.\"}".into(),
            Some(g) => format!("{{\"message\":\"Role: checker. Gate {g}\"}}"),
            None => "{}".into(),
        };
    }
    if !has(l, "\"role\":\"assistant\"") || has(l, "api-request-blob") {
        return "{}".into();
    }
    let mut kept: Vec<String> = Vec::new();
    for g in ['A', 'B', 'C'] {
        let mut s = factory::evidence::scan::Sub { nonempty: true, role: Some(g), ..Default::default() };
        s.line(l);
        kept.extend(s.last);
    }
    let mut r = factory::evidence::scan::Sub { nonempty: true, role: Some('R'), ..Default::default() };
    r.line(l);
    kept.extend(r.last);
    if has(l, "CRITICAL:") {
        kept.push("CRITICAL: x".into());
    }
    // A JSON escape (backslash, n) between matches ends each one exactly where the original did.
    let text = kept.join("\\n");
    format!("{{\"message\":{{\"role\":\"assistant\",\"content\":[{{\"type\":\"text\",\"text\":\"{text}\"}}]}}}}")
}
