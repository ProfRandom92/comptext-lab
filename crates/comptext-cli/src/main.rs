mod cli;
mod provider;
mod runtime;

fn main() {
    let code = cli::run(std::env::args().skip(1));
    std::process::exit(code);
}
