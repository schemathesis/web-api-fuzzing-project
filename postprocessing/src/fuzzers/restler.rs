use regex::Regex;
use std::{
    fs::read_to_string,
    path::{Path, PathBuf},
};

use crate::output::TestCase;

lazy_static::lazy_static! {
    static ref TEST_CASE_RE: Regex = Regex::new(r"(?s)Sending: '\w+? .+? HTTP.+?Received: 'HTTP/[0-2].[0-9] ([0-9]{3})").expect("A valid regex");
    static ref COMBINATIONS_RE: Regex = Regex::new(r"Request-[0-9]+: Value Combinations: ([0-9]+)").expect("A valid regex");
    static ref ENDPOINTS_RE: Regex = Regex::new(r"(?s)Endpoint - (.+?)\n.+?restler_static_string: '(.+?) '").expect("A valid regex");
    static ref TOTAL_RE: Regex = Regex::new(r"main_driver': ([0-9]+)").expect("A valid regex");

}

pub fn process_network_log(directory: &Path) -> impl Iterator<Item = TestCase<'static>> + 'static {
    let logs_directory = get_logs_directory(directory);
    // The network log does not display path templates, only rendered ones
    // To match those paths with templates, parse `main.txt`
    // It provides the order of endpoints that we can use when see that the network log entry
    // contains "Remaining candidate combinations: 1)" string, which means that it is the latest
    // request for this endpoint and the next block (if present) will be for another endpoint
    let main_content =
        read_to_string(logs_directory.join("main.txt")).expect("Failed to read file");
    let log_file = find_log_file(&logs_directory);
    let content = read_to_string(log_file).expect("Failed to read file");
    let total_cases = TOTAL_RE
        .captures(&main_content)
        .expect("Always present")
        .get(1)
        .expect("Always present")
        .as_str()
        .parse::<usize>()
        .expect("Invalid number");
    let mut cases = Vec::with_capacity(total_cases);
    let requests_data = process_main(&main_content);
    let mut requests = requests_data.iter();
    let (mut method, mut path) = requests.next().expect("No requests made").clone();
    let mut is_last_endpoint = false;
    for block in content.split("Generation-1: Rendering Sequence").skip(1) {
        for case in TEST_CASE_RE.captures_iter(block) {
            let status_code = case
                .get(1)
                .expect("Always present")
                .as_str()
                .parse::<u16>()
                .expect("Invalid status code");
            if (500..600).contains(&status_code) {
                cases.push(TestCase::server_error(
                    method.clone(),
                    path.clone(),
                    status_code,
                ))
            } else {
                // There are no other cases occured during testing, thus coercing everything else to `pass`
                cases.push(TestCase::pass(method.clone(), path.clone()))
            }
        }
        if block.contains("Remaining candidate combinations: 1)") {
            if let Some((m, p)) = requests.next() {
                method = m.clone();
                path = p.clone();
            } else if is_last_endpoint {
                // Health-check
                panic!("Invalid endpoints mapping");
            } else {
                is_last_endpoint = true
            }
        }
    }
    cases.into_iter()
}

fn get_logs_directory(directory: &Path) -> PathBuf {
    let results_directory = directory.join("Test/RestlerResults");
    // There is always one directory in `RestlerResults`
    let entry = results_directory
        .read_dir()
        .expect("Failed to read dir")
        .next()
        .expect("Can not find experiment directory")
        .expect("Failed to read dir")
        .path();
    entry.join("logs")
}

fn find_log_file(directory: &PathBuf) -> PathBuf {
    directory
        .read_dir()
        .expect("Failed to read dir")
        .find(|e| {
            e.as_ref()
                .expect("Failed to read dir")
                .path()
                .file_stem()
                .expect("Failed to get file stem")
                .to_string_lossy()
                .starts_with("network.testing")
        })
        .expect("Failed to find a log file")
        .expect("Failed to read entry")
        .path()
}

fn process_main(content: &str) -> Vec<(String, String)> {
    let mut out = Vec::new();
    for block in content.split("Rendering request").skip(1) {
        let captures = ENDPOINTS_RE.captures(block).expect("Always present");
        let path = captures.get(1).expect("Always present").as_str().to_owned();
        let method = captures.get(2).expect("Always present").as_str().to_owned();
        out.push((method, path))
    }
    out
}
