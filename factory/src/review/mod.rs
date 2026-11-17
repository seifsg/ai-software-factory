//! Portable review inputs and handback checks. The caller launches the reviewer and owns the gate.

mod handback;
mod packet;

pub fn cli(args: &[&str]) -> u8 {
    let result = match args {
        ["packet", args @ ..] => packet::assemble(args).map(|packet| print!("{packet}")),
        ["check", args @ ..] => handback::check(args),
        _ => {
            eprintln!(
                "usage: factory review packet --base <sha> --head <sha> [--proof <file>]... [--context <file>]... | check --role <deep|final|checker> --head <sha> [--gate <A|B|C>] [--report <file>] <handback>"
            );
            return 2;
        }
    };
    match result {
        Ok(()) => 0,
        Err(error) => {
            eprintln!("factory review: {error}");
            1
        }
    }
}
