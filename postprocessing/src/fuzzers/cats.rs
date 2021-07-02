use std::fs;
use std::fs::DirEntry;
use std::path::Path;

use globset::{Glob, GlobMatcher};
use rayon::prelude::*;
use regex::Regex;
use serde_json::Value;

use crate::{error::ProcessingError, output::TestCase};

static TEST_CASE_SEPARATOR: &str = "------------------------------------------------------------------------------------------------------------------------------------------------------";

lazy_static::lazy_static! {
    static ref PATH_CASES_RE: Regex = Regex::new(r"Start fuzzing path ").expect("A valid regex");
    static ref UNEXPECTED_RESPONSE_CODE_RE: Regex = Regex::new(r"Call returned as expected, but with undocumented code: expected \[[0-9 ,]+\], actual \[([0-9]+)\]\.").expect("A valid regex");
    static ref METHOD_RE: Regex = Regex::new(r"Protocol: HTTP/[0-9]\.[0-9], Method: ([A-Z]+), ReasonPhrase").expect("A valid regex");
    static ref FAILED_FUZZER_RE: Regex = Regex::new(r"Fuzzer \[.+?\] failed due to").expect("A valid regex");
    static ref PASSED_CASE_RE: Regex = Regex::new(r"Call returned as expected\. Response code [0-9]+ matches the contract\. Response body matches the contract!").expect("A valid regex");
    static ref TEST_FILE_RE: Regex = Regex::new(r"Test[0-9]+\.js").expect("A valid regex");
    static ref TEST_FILE_GLOB: GlobMatcher = Glob::new(r"**/Test*.js").expect("Valid pattern").compile_matcher();
}

pub fn process_stdout(content: &str) {
    // The first block contains general info about Cats, skip it.
    for block in PATH_CASES_RE.split(content).skip(1) {
        let path = extract_path(block);
        let cases: Vec<&str> = block.split(TEST_CASE_SEPARATOR).collect();
        for (idx, case) in cases.iter().enumerate() {
            if idx + 1 == cases.len()
                || is_skipped(case)
                || is_fuzzer_failure(case)
                || is_ignored_fuzzer(case)
                || is_ignored_result(case)
            {
                continue;
            }
            let method = METHOD_RE
                .captures(case)
                .expect("Always present")
                .get(1)
                .expect("Always present")
                .as_str();
            if let Some(captures) = UNEXPECTED_RESPONSE_CODE_RE.captures(case) {
                let status_code = captures
                    .get(1)
                    .expect("Always present")
                    .as_str()
                    .parse::<u16>()
                    .expect("Valid status code");
                let tc = TestCase::unexpected_status_code(method, path, status_code);
                println!("test case: {:?}", tc);
            } else if is_response_conformance_error(case) {
                let tc = TestCase::response_conformance(method, path);
                println!("{:?}", tc);
            } else if is_passed(case) {
                let tc = TestCase::pass(method, path);
            } else {
                println!("{}", case)
            }
        }
    }
}

/// Get the currently tested path.
fn extract_path(block: &str) -> &str {
    let line_end_idx = block.find("\n").expect("There is always a line end");
    &block[..line_end_idx - 1]
}

/// Whether a test case was skipped by the fuzzer.
fn is_skipped(case: &str) -> bool {
    case.contains("Skipped due to:")
}

static IGNORED_FUZZERS: [&str; 8] = [
    "NamingsContractInfoFuzzer",
    "PathTagsContractInfoFuzzer",
    "RecommendedHeadersContractInfoFuzzer",
    "TopLevelElementsContractInfoFuzzer",
    "VersionsContractInfoFuzzer",
    "XmlContentTypeContractInfoFuzzer",
    "CheckSecurityHeadersFuzzer",
    "UnsupportedAcceptHeadersFuzzer",
];
/// Whether it is a fuzzer's failure.
fn is_fuzzer_failure(case: &str) -> bool {
    FAILED_FUZZER_RE.is_match(case)
}

/// Is this fuzzer ignored?
fn is_ignored_fuzzer(case: &str) -> bool {
    IGNORED_FUZZERS.iter().any(|f| case.contains(f))
}

fn is_ignored_result(case: &str) -> bool {
    case.contains("Call returned an unexpected result, but with documented code: expected")
}

fn is_passed(case: &str) -> bool {
    case.contains("Request failed as expected for http method") || PASSED_CASE_RE.is_match(case)
}

fn is_response_conformance_error(string: &str) -> bool {
    string.contains("Response body does NOT match the contract!")
}

pub(crate) fn process_files(directory: &Path) -> Result<(), ProcessingError> {
    let paths: Vec<_> = fs::read_dir(directory)?
        .filter_map(|entry| {
            if let Ok(entry) = entry {
                if TEST_FILE_GLOB.is_match(entry.path()) {
                    Some(entry)
                } else {
                    None
                }
            } else {
                None
            }
        })
        .collect();
    let cases: Vec<Result<_, ProcessingError>> = paths.par_iter().map(process_file).collect();
    Ok(())
}

fn process_file(entry: &DirEntry) -> Result<Option<TestCase>, ProcessingError> {
    let data = read_json(entry)?;
    if let Some(path) = data["path"].as_str() {
        let details = data["resultDetails"].as_str().expect("Always a string");
        if let Some(captures) = UNEXPECTED_RESPONSE_CODE_RE.captures(details) {
            let status_code = captures
                .get(1)
                .expect("Always present")
                .as_str()
                .parse::<u16>()
                .expect("Valid status code");
            let method = data["response"]["httpMethod"]
                .as_str()
                .expect("Always present");
            return Ok(Some(TestCase::unexpected_status_code(
                method.to_owned(),
                path.to_owned(),
                status_code,
            )));
        }
        let fuzzer = data["fuzzer"].as_str().expect("Always a string");
        if is_ignored_result(details) || is_ignored_fuzzer(fuzzer) {
            return Ok(None);
        }

        let method = data["response"]["httpMethod"]
            .as_str()
            .expect("Always present");
        if is_response_conformance_error(details) {
            return Ok(Some(TestCase::response_conformance(
                method.to_owned(),
                path.to_owned(),
            )));
        }
        if is_passed(details) {
            return Ok(Some(TestCase::pass(method.to_owned(), path.to_owned())));
        }
        //println!("{}", data);
        Ok(Some(TestCase::pass(method.to_owned(), path.to_owned())))
    } else {
        Ok(None)
    }
}

fn read_json(entry: &DirEntry) -> Result<Value, ProcessingError> {
    let content = fs::read_to_string(entry.path())?;
    let json_start_idx = content.find('{').expect("Always present");
    serde_json::from_str(&content[json_start_idx..]).map_err(ProcessingError::Json)
}
