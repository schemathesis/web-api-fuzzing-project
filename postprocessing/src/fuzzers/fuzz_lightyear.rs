use crate::output::{ErrorKind, FailureKind, SkipKind, TestCase, TestCaseResult};
use regex::Regex;

lazy_static::lazy_static! {
    static ref TEST_CASE_RE: Regex = Regex::new(r"_* ?[A-Za-z\._]*? \[\w+\] ? _*").expect("Valid regex");
}

pub fn process_stdout(content: &str) -> impl Iterator<Item = TestCase> {
    let failures = if let Some(failures_start_idx) = content
        .find("================================ Test Failures ================================")
    {
        &content[failures_start_idx..]
    } else {
        ""
    };
    TEST_CASE_RE.split(failures).filter_map(process_case)
}

fn should_skip(case: &str) -> bool {
    case.contains("422 UNPROCESSABLE ENTITY")
        || case.contains("400 BAD REQUEST")
        || case.contains("404 NOT FOUND")
}

fn is_error(case: &str) -> bool {
    case.contains("SwaggerMappingError")
}

fn is_response_conformance_failure(case: &str) -> bool {
    case.contains("jsonschema.exceptions.ValidationError")
}

fn is_server_error(case: &str) -> bool {
    case.contains("HTTPInternalServerError")
}

fn process_case(case: &str) -> Option<TestCase> {
    let method: Option<std::borrow::Cow<'_, str>> = None;
    let path: Option<std::borrow::Cow<'_, str>> = None;
    if should_skip(case) {
        Some(TestCase::new(
            method,
            path,
            TestCaseResult::Skip {
                kind: SkipKind::NotInteresting,
                reason: "Reports regular 422, 400, 404 as failures".to_string(),
            },
        ))
    } else if is_error(case) {
        Some(TestCase::error(method, path, ErrorKind::Internal))
    } else if is_response_conformance_failure(case) {
        Some(TestCase::new(
            method,
            path,
            TestCaseResult::Failure {
                kind: FailureKind::ResponseConformance,
            },
        ))
    } else if is_server_error(case) {
        Some(TestCase::new(
            method,
            path,
            TestCaseResult::Failure {
                kind: FailureKind::ServerError { status_code: 500 },
            },
        ))
    } else {
        None
    }
}
