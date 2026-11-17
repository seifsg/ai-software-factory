//! `factory`: the run guard and the free checks of the AI Software Factory, one native binary.

use std::process::ExitCode;

const USAGE: &str = "usage: factory <command>
  guard stop|compact          hook JSON on stdin
  guard check [<session id>]  with an id: the Stop rules as one line; without: gate backing
  guard clear [<run folder>]  the owner's command after a halt
  guard step <n|Tk> < block    in the run's folder
  doctor [<plugin root>] [--fix]
  update-check [<plugin root>]
  lint <A|B|C> [--skills <dir>] [<run folder>]
  contracts [--skills <dir>] <skill>...
  review packet --base <sha> --head <sha> [--proof <file>]... [--context <file>]...
  review check --role <deep|final|checker> --head <sha> [--gate <A|B|C>] [--report <file>] <handback>
  tree [<folder>]
  proof-hash <file>...
  receipt run [--suite <name>] -- <command>...
  receipt write --cmd <command> (--exit <code> | --result PASS|FAIL) [--suite <name>] [--secs <n>] [--log <path>]
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
        ["review", rest @ ..] => factory::review::cli(rest),
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
