//! `contracts`: prints only the `## Output contract` section of each named skill, the part a checker
//! needs, so its brief never carries the rest of the method.

use std::path::{Path, PathBuf};

/// The `## Output contract` section of a SKILL.md (its heading up to the next `## ` heading), trimmed.
pub fn extract(text: &str) -> Option<String> {
    let mut out: Vec<&str> = Vec::new();
    let mut on = false;
    let mut fence = false;
    for l in text.lines() {
        if on && !fence && l.starts_with("## ") {
            break;
        }
        if l == "## Output contract" {
            on = true;
        }
        if on {
            if l.trim_start().starts_with("```") {
                fence = !fence;
            }
            out.push(l);
        }
    }
    while out.last().is_some_and(|l| l.trim().is_empty()) {
        out.pop();
    }
    (!out.is_empty()).then(|| out.join("\n"))
}

/// Where skills live: `--skills`, `FACTORY_SKILLS`, the plugin folder beside this binary, or `.agents/skills`.
pub fn skills_dir(flag: Option<&str>) -> Option<PathBuf> {
    if let Some(f) = flag {
        return Some(PathBuf::from(crate::paths::norm(f)));
    }
    if let Some(e) = std::env::var_os("FACTORY_SKILLS").filter(|v| !v.is_empty()) {
        return Some(PathBuf::from(crate::paths::norm(&e.to_string_lossy())));
    }
    let beside = std::env::current_exe().ok().and_then(|p| Some(p.parent()?.parent()?.join("skills")));
    if let Some(b) = beside.filter(|b| b.join("safe-factory/SKILL.md").is_file()) {
        return Some(b);
    }
    let mut d = Some(crate::guard::cwd());
    while let Some(dir) = d {
        let s = dir.join(".agents/skills");
        if s.join("safe-factory/SKILL.md").is_file() {
            return Some(s);
        }
        d = dir.parent().map(Path::to_path_buf);
    }
    None
}

/// The contract text of one skill, or an error naming what is missing.
pub fn of(skills: &Path, skill: &str) -> Result<String, String> {
    let p = skills.join(skill).join("SKILL.md");
    let text = std::fs::read_to_string(&p).map_err(|_| format!("no skill {skill} in {}", crate::paths::text(skills)))?;
    extract(&text).ok_or_else(|| format!("{skill} has no ## Output contract"))
}

/// `factory contracts [--skills <dir>] <skill>...`
pub fn cli(args: &[&str]) -> u8 {
    let flag = crate::receipt::opt(args, "--skills");
    let names: Vec<&str> =
        args.iter().enumerate().filter(|(i, a)| **a != "--skills" && (*i == 0 || args[i - 1] != "--skills")).map(|(_, a)| *a).collect();
    if names.is_empty() {
        eprintln!("usage: factory contracts [--skills <dir>] <skill>...");
        return 2;
    }
    let Some(dir) = skills_dir(flag) else {
        eprintln!("factory contracts: no skills folder found; pass --skills <dir>");
        return 1;
    };
    let mut out = Vec::new();
    for n in names {
        match of(&dir, n) {
            Ok(c) => out.push(format!("# {n}\n{c}\n")),
            Err(e) => {
                eprintln!("factory contracts: {e}");
                return 1;
            }
        }
    }
    print!("{}", out.join("\n"));
    0
}

#[cfg(test)]
mod tests {
    #[test]
    fn takes_only_the_contract() {
        let t = "# S\n\n## Steps\nx\n\n## Output contract\n\n- [ ] **A:** y\n```text\n## not a heading\n```\n\n## Later\nz\n";
        assert_eq!(super::extract(t).unwrap(), "## Output contract\n\n- [ ] **A:** y\n```text\n## not a heading\n```");
    }
}
