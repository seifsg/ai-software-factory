//! Dev-only timing of guard calls in-process (no process start): `cargo run --release --example bench -- <hook json file> [n]`.
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let Some(file) = args.first() else {
        eprintln!("usage: bench <hook json file> [n]");
        std::process::exit(2);
    };
    let n: usize = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(10);
    let input = factory::hook::Input::parse(&std::fs::read(file).expect("read input"));
    let here = std::env::current_dir().expect("cwd");
    for i in 0..n {
        let t = Instant::now();
        let r = factory::guard::flow::run(&input, factory::guard::flow::Mode::Stop, &here);
        let ms = t.elapsed().as_secs_f64() * 1000.0;
        if i == 0 {
            eprintln!("{}", r.map(|r| r.inner().chars().take(80).collect::<String>()).unwrap_or_default());
        }
        println!("call {i}: {ms:.2} ms");
    }
}
