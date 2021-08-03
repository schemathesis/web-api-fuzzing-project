use crate::output::{ErrorKind, SkipKind, TestCase};
use regex::Regex;

lazy_static::lazy_static! {
    static ref TEST_CASE_RE: Regex = Regex::new(r"\d+\) Got Swag\? http://0.0.0.0:\d+/.+?: ").expect("Valid regex");
    static ref METHOD_PATH_RE: Regex = Regex::new(r"(\w+?) (.+?) Monkey Test").expect("Valid regex");
    static ref SERVER_ERROR_RE: Regex = Regex::new(r"Status (5\d{2}) detected").expect("Valid regex");
    static ref UNEXPECTED_STATUS_CODE_RE: Regex = Regex::new(r"Unexpected response status (\d{3})").expect("Valid regex");
}

pub fn process_stdout(content: &str) -> impl Iterator<Item = TestCase> {
    TEST_CASE_RE.split(content).skip(1).map(process_case)
}

fn is_error(case: &str) -> bool {
    case.contains("write EPROTO")
}

fn is_response_conformance_failure(case: &str) -> bool {
    case.contains("is not of a type(s) ") | case.contains("does not conform to the")
}

fn process_case(case: &str) -> TestCase {
    let captures = METHOD_PATH_RE.captures(case).expect("Always present");
    let method = captures.get(1).expect("Always present").as_str();
    let path = captures.get(2).expect("Always present").as_str();
    if case.contains("Error: done() invoked with non-Error: Could not authenticate") {
        TestCase::skip(
            method,
            path,
            SkipKind::CanNotTest,
            "Missing auth".to_string(),
        )
    } else if case.contains("Could not GET") {
        TestCase::skip(
            method,
            path,
            SkipKind::CanNotTest,
            "Can not make a GET request".to_string(),
        )
    } else if case.contains("Invalid data") {
        TestCase::skip(
            method,
            path,
            SkipKind::InvalidAssumption,
            "Concludes failure if data is not object or falsy".to_string(),
        )
    } else if case.contains("Body should be empty") {
        TestCase::skip(
            method,
            path,
            SkipKind::InvalidAssumption,
            "Expects empty body if schema is an empty object".to_string(),
        )
    } else if is_error(case) {
        TestCase::error(Some(method), Some(path), ErrorKind::Internal)
    } else if is_response_conformance_failure(case) {
        TestCase::response_conformance(method, path)
    } else if let Some(captures) = UNEXPECTED_STATUS_CODE_RE.captures(case) {
        let status_code = captures
            .get(1)
            .expect("Always present")
            .as_str()
            .parse::<u16>()
            .expect("Invalid status code");
        if (500..600).contains(&status_code) {
            TestCase::server_error(method, path, status_code)
        } else {
            TestCase::unexpected_status_code(method, path, status_code)
        }
    } else if let Some(captures) = SERVER_ERROR_RE.captures(case) {
        let status_code = captures
            .get(1)
            .expect("Always present")
            .as_str()
            .parse::<u16>()
            .expect("Invalid status code");
        TestCase::server_error(method, path, status_code)
    } else {
        panic!("Unknown test case")
    }
}
