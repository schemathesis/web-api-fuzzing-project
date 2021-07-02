mod core;
mod error;
mod fuzzers;
mod output;
use std::path::PathBuf;
use structopt::StructOpt;

#[derive(StructOpt, Debug)]
#[structopt(name = "postprocess")]
struct Opt {
    /// Artifacts directory
    #[structopt(name = "DIRECTORY", parse(from_os_str))]
    directory: PathBuf,

    /// Fuzzer output to process
    #[structopt(short, long)]
    fuzzer: Vec<fuzzers::Fuzzer>,

    /// Target output to process
    #[structopt(short, long)]
    target: Vec<String>,
    /// Sequential run index
    #[structopt(short, long)]
    idx: Vec<String>,
}

fn main() {
    let opt = Opt::from_args();
    core::process(&opt.directory, &opt.fuzzer, &opt.target, &opt.idx).expect("Processing error");
}
