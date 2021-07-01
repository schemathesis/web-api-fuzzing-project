use std::path::Path;

use crate::{
    error::ProcessingError,
    output::{FailureKind, TestCase, TestCaseResult},
};
use regex::Regex;

lazy_static::lazy_static! {
    static ref TEST_CASE_RE: Regex = Regex::new(r"[0-9]+ \[INFO\] kitty: Current test: [0-9]+").expect("A valid regex");
    static ref PATH_PARAMETERS_RE: Regex = Regex::new(r"[0-9]+ \[INFO\] kitty: Compiled url in (.+?), out:").expect("A valid regex");
    static ref URL_RE: Regex = Regex::new(r"[0-9]+ \[INFO\] kitty: Request URL : b'(\w+?)' (.+?)[\r?]").expect("A valid regex");
    static ref METHOD_RE: Regex = Regex::new(r"[0-9]+ \[INFO\] kitty: Request URL : b'(\w+?)'").expect("A valid regex");
    static ref STATUS_CODE_RE: Regex = Regex::new(r"is not in the expected list:', ([0-9]+?)\)").expect("A valid regex");
}

const CURL_ERROR: &str = "pycurl.error: (3, '')";

pub fn process(directory: &Path) -> Result<(), ProcessingError> {
    let output_path = directory.join("stdout.txt");
    let content = std::fs::read_to_string(output_path)?;
    parse(&content);
    Ok(())
}

pub fn parse(content: &str) {
    for block in TEST_CASE_RE.split(content) {
        let _result = parse_one(block);
        // TODO. store result
    }
}

fn parse_one(block: &str) -> TestCase {
    let capture = PATH_PARAMETERS_RE.captures(block);
    let (method, url) = if let Some(cap) = capture {
        // URL contains path parameters - extract them
        let url = cap.get(1).expect("Always present").as_str();
        let method = METHOD_RE
            .captures(block)
            .expect("Always present")
            .get(1)
            .expect("Always present")
            .as_str();
        (method, url)
    } else {
        // Only a compiled URL is present - take it up to query parameters
        let capture = URL_RE.captures(block).expect("Always present");
        let method = capture.get(1).expect("Always present").as_str();
        let url = capture.get(2).expect("Always present").as_str();
        (method, url)
    };
    if block.contains(CURL_ERROR) {
        // cURL error
        TestCase::new(method, url, TestCaseResult::Error)
    } else if let Some(mat) = STATUS_CODE_RE.captures(block) {
        // Failed with an unexpected status code
        let status_code = mat
            .get(1)
            .expect("Always present")
            .as_str()
            .parse::<u16>()
            .expect("Valid status code");
        TestCase::new(
            method,
            url,
            TestCaseResult::Failure(FailureKind::UnexpectedStatusCode(status_code)),
        )
    } else {
        // Passed test
        TestCase::new(method, url, TestCaseResult::Pass)
    }
}
