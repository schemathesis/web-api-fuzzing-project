use regex::Regex;
use serde::ser::{SerializeSeq, Serializer};
use std::{
    collections::{HashMap, HashSet},
    fs::{read_to_string, File},
    path::{Path, PathBuf},
};

use crate::output::TestCase;

lazy_static::lazy_static! {
    static ref TEST_CASE_RE: Regex = Regex::new(r"(?s)Sending: '(\w+?) (.+?) HTTP.+?Received: 'HTTP/[0-2].[0-9] ([0-9]{3})").expect("A valid regex");
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
    for block in content.split("Generation-1: Rendering Sequence").skip(1) {
        for case in TEST_CASE_RE.captures_iter(block) {
            let method = case.get(1).expect("Always present").as_str().to_string();
            let path = case.get(2).expect("Always present").as_str();
            let p = url::Url::parse(&format!("http://example.com{}", path)).unwrap();
            let path = p.path().to_string();
            let status_code = case
                .get(3)
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

#[derive(serde::Deserialize, Hash, PartialEq, Eq, Debug)]
struct BucketData {
    request: RequestDataWrapper,
    response: ResponseDataWrapper,
}
#[derive(serde::Deserialize, Hash, PartialEq, Eq, Debug)]
struct RequestDataWrapper {
    RequestData: RequestData,
}
#[derive(serde::Deserialize, Hash, PartialEq, Eq, Debug)]
struct RequestData {
    method: String,
    path: String,
    query: String,
    body: String,
}
#[derive(serde::Deserialize, Hash, PartialEq, Eq, Debug)]
struct ResponseDataWrapper {
    ResponseData: ResponseData,
}
#[derive(serde::Deserialize, Hash, PartialEq, Eq, Debug)]
struct ResponseData {
    code: u16,
    content: String,
}

#[derive(serde::Serialize)]
struct StdoutEntry<'a> {
    method: &'a str,
    path: &'a str,
    failures: HashMap<&'static str, u16>,
}

pub(crate) fn get_deduplicated_results(directory: &Path, out_directory: &PathBuf) {
    let error_buckets_file = directory.join("Test/ResponseBuckets/errorBuckets.json");
    let file = File::open(error_buckets_file).unwrap();
    let data: serde_json::Value = serde_json::from_reader(file).unwrap();

    let mut network_data = HashSet::new();
    for (status_code, buckets) in data.as_object().unwrap() {
        if status_code.starts_with('5') {
            for array in buckets.as_object().unwrap().values() {
                for pair in array.as_array().unwrap() {
                    let entry: BucketData =
                        serde_json::from_value(pair.clone()).unwrap_or_else(|_| panic!("{}", pair));
                    network_data.insert(entry);
                }
            }
        }
    }
    if !network_data.is_empty() {
        let output_path = out_directory.join("deduplicated_cases.json");
        let output_file = File::create(output_path).expect("Failed to create a file");
        let mut ser = serde_json::Serializer::new(output_file);
        let mut seq = ser.serialize_seq(Some(network_data.len())).unwrap();
        let mut map = HashMap::with_capacity(network_data.len());
        for entry in network_data {
            let method = entry.request.RequestData.method;
            let path = entry.request.RequestData.path;
            let e = map.entry((method, path)).or_insert_with(HashMap::new);
            let x = e.entry("server_error").or_insert(0);
            *x += 1;
        }
        for ((method, path), failures) in map {
            seq.serialize_element(&StdoutEntry {
                method: &method,
                path: &path,
                failures,
            })
            .unwrap()
        }
        seq.end().unwrap();
    }
}
