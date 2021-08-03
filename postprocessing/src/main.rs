mod core;
mod error;
mod fuzzers;
mod output;
mod search;
mod sentry;
use std::{env, path::PathBuf};
use structopt::StructOpt;

#[derive(StructOpt, Debug)]
#[structopt(name = "postprocess")]
struct CommandOptions {
    #[structopt(name = "COMMAND")]
    command: String,

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
    match env::args().nth(1).as_deref() {
        Some("parse-fuzzers-output") => {
            let options = CommandOptions::from_args();
            core::process(
                &options.directory,
                &options.fuzzer,
                &options.target,
                &options.idx,
            )
            .expect("Processing error");
        }
        Some("parse-sentry-events") => {
            let options = CommandOptions::from_args();
            sentry::parse_events(
                &options.directory,
                &options.fuzzer,
                &options.target,
                &options.idx,
            )
            .expect("Processing error");
        }
        Some(command) => panic!("Unknown command: {}", command),
        None => panic!("Missing command"),
    }
}
