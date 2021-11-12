use serde::ser::{SerializeSeq, Serializer};
use std::{
    collections::HashMap,
    fs::{read_to_string, File},
    io::{BufRead, BufReader},
    path::{Path, PathBuf},
};

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
    context: Option<serde_json::Value>,
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
            (Status::Failure, "content_type_conformance") => match check.context {
                Some(context) => match context["type"].as_str() {
                    Some("malformed_media_type") => TestCase::malformed_media_type(method, path),
                    Some("missing_content_type") => TestCase::missing_content_type(method, path),
                    _ => TestCase::content_type_conformance(method, path),
                },
                None => TestCase::content_type_conformance(method, path),
            },
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
    static ref TEST_CASE2_RE: Regex = Regex::new(r"state.schema\['(.+?)'\]\['(.+?)'\]").expect("Valid regex");
    static ref ERROR_RE: Regex = Regex::new(r"_step\(case=state\.schema\['(.+?)'\]\['(\w+?)']").expect("Valid regex");
    static ref STDOUT_FAILURE_RE: Regex = Regex::new(r"^[0-9]+\. ").expect("Valid regex");
    static ref SERVER_ERROR_RE: Regex = Regex::new(r"Received a response with 5xx status code: ([0-9]+)").expect("Valid regex");
    static ref UNEXPECTED_STATUS_CODE: Regex = Regex::new(r"Received a response with a status code, which is not defined in the schema: ([0-9]+)").expect("Valid regex");
    static ref UNEXPECTED_CONTENT_TYPE: Regex = Regex::new(r"Received a response with '(.+?)' Content-Type, but it is not declared in the schema.").expect("Valid regex");

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
        let capture = TEST_CASE_RE.captures(case).expect("Always matches");
        let capture2 = TEST_CASE2_RE
            .captures_iter(case)
            .last()
            .expect("Always matches");
        let error = capture.get(1).expect("Always present");
        let method = capture2
            .get(2)
            .expect("Always present")
            .as_str()
            .to_ascii_uppercase();
        let path = capture2.get(1).expect("Always present").as_str().to_owned();
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

#[derive(serde::Serialize)]
struct StdoutEntry<'a> {
    method: &'a str,
    path: &'a str,
    failures: HashMap<&'static str, u16>,
}

pub(crate) fn get_deduplicated_results(directory: &Path, out_directory: &PathBuf) {
    let path = directory.join("stdout.txt");
    let content = read_to_string(path).expect("Failed to read stdout.txt");
    if !content.contains("FAILURES") {
        return;
    }
    let mut lines = content
        .lines()
        .filter_map(|l| {
            let trimmed = l.trim();
            if trimmed.ends_with("[P]") || trimmed.ends_with("[N]") || STDOUT_FAILURE_RE.is_match(l)
            {
                Some(trimmed)
            } else {
                None
            }
        })
        .peekable();
    let output_path = out_directory.join("deduplicated_cases.json");
    let output_file = File::create(output_path).expect("Failed to create a file");
    let mut ser = serde_json::Serializer::new(output_file);
    let mut seq = ser.serialize_seq(None).unwrap();
    while let Some(line) = lines.next() {
        if line.ends_with("[P]") || line.ends_with("[N]") {
            // New endpoint
            let mut parts = line.split_ascii_whitespace();
            let method = parts.next().unwrap();
            let path = parts.next().unwrap();
            while let Some(true) = lines.peek().map(|l| STDOUT_FAILURE_RE.is_match(l)) {
                if let Some(next) = lines.peek() {
                    if let Some(captures) = SERVER_ERROR_RE.captures(next) {
                        let status_code = captures.get(1).unwrap().as_str().parse::<u16>().unwrap();
                        seq.serialize_element(&TestCase::server_error(method, path, status_code))
                            .unwrap();
                    } else if next.contains("Response timed out after") {
                        seq.serialize_element(&TestCase::request_timeout(method, path))
                            .unwrap();
                    } else if next
                        .contains("The received response does not conform to the defined schema")
                    {
                        seq.serialize_element(&TestCase::response_conformance(method, path))
                            .unwrap();
                    } else if let Some(captures) = UNEXPECTED_STATUS_CODE.captures(next) {
                        let status_code = captures.get(1).unwrap().as_str().parse::<u16>().unwrap();
                        seq.serialize_element(&TestCase::unexpected_status_code(
                            method,
                            path,
                            status_code,
                        ))
                        .unwrap();
                    } else if UNEXPECTED_CONTENT_TYPE.captures(next).is_some() {
                        seq.serialize_element(&TestCase::content_type_conformance(method, path))
                            .unwrap();
                    } else if next.contains("Response is missing the `Content-Type` header") {
                        seq.serialize_element(&TestCase::missing_content_type(method, path))
                            .unwrap();
                    } else if next.contains("Malformed media type") {
                        seq.serialize_element(&TestCase::malformed_media_type(method, path))
                            .unwrap();
                    } else {
                        panic!("Unknown failure: {}", next)
                    }
                }
                lines.next();
            }
        } else {
            unreachable!("Should not happen")
        }
    }
    SerializeSeq::end(seq).unwrap();
}
