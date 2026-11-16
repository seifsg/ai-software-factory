//! `factory`: the run guard and the free checks of the AI Software Factory, one native binary.

use std::process::ExitCode;

const USAGE: &str = "usage: factory <command>
  guard stop|compact          hook JSON on stdin
  guard check <session id>    a host with no command hook
  guard clear [<run folder>]  the owner's command after a halt
  guard step <n|Tk> [--session <id>] < block
  doctor [<plugin root>] [--fix]
  update-check [<plugin root>]
  lint <A|B|C> [--skills <dir>] [<run folder>]
  contracts [--skills <dir>] <skill>...
  tree [<folder>]
  proof-hash <file>...
  receipt run [--suite <name>] -- <command>...
  receipt write --suite <name> --result PASS|FAIL --cmd <command> [--secs <n>]
  receipt check [--commit <sha>] [--suite <name>]
  --version";

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let a: Vec<&str> = args.iter().map(String::as_str).collect();
    let code = match a.as_slice() {
        ["--version" | "-V"] => {
            println!("factory {}", factory::VERSION);
            0
        }
        ["guard", rest @ ..] => factory::guard::cli(rest),
        ["doctor", rest @ ..] => factory::doctor::cli(rest),
        ["update-check", rest @ ..] => factory::update::cli(rest),
        ["lint", rest @ ..] => factory::lint::cli(rest),
        ["contracts", rest @ ..] => factory::contracts::cli(rest),
        ["tree", rest @ ..] => factory::git::tree::cli(rest),
        ["proof-hash", rest @ ..] => factory::proof::cli(rest),
        ["receipt", rest @ ..] => factory::receipt::cli(rest),
        _ => {
            eprintln!("{USAGE}");
            2
        }
    };
    ExitCode::from(code)
}
