use std::{
    fs::File,
    io::{BufRead, BufReader},
    path::Path,
};
use url::Url;

use regex::Regex;

use crate::output::{ErrorKind, TestCase};

pub fn process_debug_output(directory: &Path) -> impl Iterator<Item = TestCase<'static>> {
    let path = directory.join("out.jsonl");
    let file = File::open(path).expect("Can't read file");
    BufReader::new(file)
        .lines()
        .map(|line| read_event(&line.expect("Can't read line")))
        .filter(filter_after_execution)
        .flat_map(parse_event)
}

fn read_event(line: &str) -> serde_json::Value {
    serde_json::from_str(line).expect("Invalid JSON")
}

fn filter_after_execution(event: &serde_json::Value) -> bool {
    event["event_type"]
        .as_str()
        .expect("This field should be a string")
        == "AfterExecution"
}

#[derive(serde::Deserialize)]
struct AfterExecution {
    result: SerializedTestResult,
}
#[derive(serde::Deserialize)]
struct SerializedTestResult {
    method: String,
    path: String,
    checks: Vec<SerializedCheck>,
}

#[derive(serde::Deserialize, Debug, Eq, PartialEq, Copy, Clone)]
#[serde(rename_all = "lowercase")]
pub(crate) enum Status {
    /// Successful test - no errors found.
    Success,
    /// Schemathesis found some failures.
    Failure,
    /// Internal Schemathesis error.
    Error,
}

#[derive(serde::Deserialize, Debug)]
pub(crate) struct SerializedCheck {
    /// A name of a Python function that was executed.
    name: String,
    /// Check result.
    value: Status,
    response: Option<Response>,
}

#[derive(serde::Deserialize, Debug)]
pub(crate) struct Response {
    status_code: u16,
}

fn parse_event(event: serde_json::Value) -> impl Iterator<Item = TestCase<'static>> {
    let parsed: AfterExecution = serde_json::from_value(event).expect("Can not parse event");
    let result = parsed.result;
    let method = result.method;
    let path = result.path;
    result.checks.into_iter().map(move |check| {
        let (method, path) = (method.clone(), path.clone());
        match (check.value, check.name.as_str()) {
            (Status::Success, _) => TestCase::pass(method, path),
            (Status::Failure, "not_a_server_error") => TestCase::server_error(
                method,
                path,
                check
                    .response
                    .expect("Response should be present")
                    .status_code,
            ),
            (Status::Failure, "status_code_conformance") => TestCase::unexpected_status_code(
                method,
                path,
                check
                    .response
                    .expect("Response should be present")
                    .status_code,
            ),
            (Status::Failure, "content_type_conformance") => {
                TestCase::content_type_conformance(method, path)
            }
            (Status::Failure, "response_headers_conformance") => {
                TestCase::response_headers_conformance(method, path)
            }
            (Status::Failure, "response_schema_conformance") => {
                TestCase::response_conformance(method, path)
            }
            (Status::Failure, "request_timeout") => TestCase::request_timeout(method, path),
            (Status::Error, _) => TestCase::error(Some(method), Some(path), ErrorKind::Internal),
            (_, _) => panic!("Unknown check"),
        }
    })
}

lazy_static::lazy_static! {
    static ref TEST_CASE_RE: Regex = Regex::new(r"(?s)[0-9]+?\. (.+?): .+  requests\.(\w+)\('(.+?)'").expect("Valid regex");
    static ref ERROR_RE: Regex = Regex::new(r"_step\(case=state\.schema\['(.+?)'\]\['(\w+?)']").expect("Valid regex");
}

pub fn process_pytest_output(content: &str) -> impl Iterator<Item = TestCase> {
    if content.contains("hypothesis.errors.MultipleFailures") {
        let (_, output) = content
            .split_once(
                "---------------------------------- Hypothesis ----------------------------------",
            )
            .expect("Always present");
        {
            let failures: Vec<TestCase> = output
                .split("Falsifying example:")
                .skip(1)
                .map(parse_case)
                .collect();
            failures.into_iter()
        }
    } else if content.contains("== FAILURES ==") {
        vec![parse_case(content)].into_iter()
    } else {
        vec![].into_iter()
    }
}

fn is_flaky(case: &str) -> bool {
    case.contains("hypothesis.errors.Flaky: Unreliable assumption")
        || case.contains("hypothesis.errors.Flaky: Inconsistent data generation!")
}

fn parse_case(case: &str) -> TestCase {
    if case.contains("InvalidSchema:") {
        let captures = ERROR_RE.captures(case).expect("Always matches");
        let method = captures.get(1).expect("Always present").as_str();
        let path = captures.get(2).expect("Always present").as_str();
        TestCase::error(Some(method), Some(path), ErrorKind::Schema)
    } else if is_flaky(case) {
        let method: Option<std::borrow::Cow<'_, str>> = None;
        let path: Option<std::borrow::Cow<'_, str>> = None;
        TestCase::error(method, path, ErrorKind::Flaky)
    } else if case.contains("hypothesis.errors.Unsatisfiable:") {
        let method: Option<std::borrow::Cow<'_, str>> = None;
        let path: Option<std::borrow::Cow<'_, str>> = None;
        TestCase::error(method, path, ErrorKind::Unsatisfiable)
    } else {
        if TEST_CASE_RE.captures(case).is_none() {
            println!("Case: {}", case);
        }
        let capture = TEST_CASE_RE.captures(case).expect("Always matches");
        let error = capture.get(1).expect("Always present");
        let method = capture
            .get(2)
            .expect("Always present")
            .as_str()
            .to_ascii_uppercase();
        let path = Url::parse(capture.get(3).expect("Always present").as_str())
            .expect("Invalid URL")
            .path()
            .to_owned();
        match error.as_str() {
            "Received a response with 5xx status code" => {
                let status_code = case[error.end() + 2..error.end() + 5]
                    .parse::<u16>()
                    .expect("Invalid integer");
                TestCase::server_error(method, path, status_code)
            }
            _ => panic!("Unknown test case"),
        }
    }
}
