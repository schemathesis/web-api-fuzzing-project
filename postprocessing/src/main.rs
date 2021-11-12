mod core;
mod error;
mod fuzzers;
mod metadata;
mod output;
mod search;
mod sentry;
mod targets;
use std::{fs::create_dir_all, path::PathBuf};
use structopt::StructOpt;

#[derive(StructOpt, Debug)]
#[structopt(name = "postprocess")]
struct CommandOptions {
    #[structopt(name = "COMMAND")]
    command: String,

    /// Artifacts directory
    #[structopt(name = "IN-DIRECTORY", parse(from_os_str))]
    in_directory: PathBuf,

    /// Output directory
    #[structopt(name = "OUT-DIRECTORY", parse(from_os_str))]
    out_directory: PathBuf,

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
    let options = CommandOptions::from_args();
    match options.command.as_str() {
        "parse-fuzzers-output" => {
            create_dir_all(&options.out_directory).expect("Failed to create OUT-DIRECTORY");
            core::process(
                &options.in_directory,
                &options.out_directory,
                &options.fuzzer,
                &options.target,
                &options.idx,
            )
            .expect("Fuzzers output processing error");
        }
        "parse-targets-output" => {
            create_dir_all(&options.out_directory).expect("Failed to create OUT-DIRECTORY");
            targets::process(
                &options.in_directory,
                &options.out_directory,
                &options.fuzzer,
                &options.target,
                &options.idx,
            )
            .expect("Targets output processing error");
        }
        "parse-sentry-events" => {
            create_dir_all(&options.out_directory).expect("Failed to create OUT-DIRECTORY");
            sentry::parse_events(
                &options.in_directory,
                &options.out_directory,
                &options.fuzzer,
                &options.target,
                &options.idx,
            )
            .expect("Sentry events processing error");
        }
        "parse-all" => {
            create_dir_all(&options.out_directory).expect("Failed to create OUT-DIRECTORY");
            core::process(
                &options.in_directory,
                &options.out_directory,
                &options.fuzzer,
                &options.target,
                &options.idx,
            )
            .expect("Fuzzers output processing error");
            targets::process(
                &options.in_directory,
                &options.out_directory,
                &options.fuzzer,
                &options.target,
                &options.idx,
            )
            .expect("Targets output processing error");
            sentry::parse_events(
                &options.in_directory,
                &options.out_directory,
                &options.fuzzer,
                &options.target,
                &options.idx,
            )
            .expect("Sentry events processing error");
        }
        command => panic!("Unknown command: {}", command),
    }
}
