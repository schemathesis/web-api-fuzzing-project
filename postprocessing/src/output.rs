use std::borrow::Cow;

#[derive(Debug, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "type")]
pub enum TestCaseResult {
    Pass,
    Failure { kind: FailureKind },
    Error,
}
#[derive(Debug, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "type")]
pub enum FailureKind {
    ServerError { status_code: u16 },
    UnexpectedStatusCode { status_code: u16 },
    ResponseConformance,
}

#[derive(Debug, serde::Serialize)]
pub struct TestCase<'a> {
    method: Cow<'a, str>,
    path: Cow<'a, str>,
    result: TestCaseResult,
}

impl<'a> TestCase<'a> {
    pub fn new(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
        result: TestCaseResult,
    ) -> TestCase<'a> {
        TestCase {
            method: method.into(),
            path: path.into(),
            result,
        }
    }
    pub fn pass(method: impl Into<Cow<'a, str>>, path: impl Into<Cow<'a, str>>) -> TestCase<'a> {
        TestCase::new(method, path, TestCaseResult::Pass)
    }
    pub fn error(method: impl Into<Cow<'a, str>>, path: impl Into<Cow<'a, str>>) -> TestCase<'a> {
        TestCase::new(method, path, TestCaseResult::Error)
    }
    pub fn server_error(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
        status_code: u16,
    ) -> TestCase<'a> {
        TestCase::new(
            method,
            path,
            TestCaseResult::Failure {
                kind: FailureKind::ServerError { status_code },
            },
        )
    }
    pub fn unexpected_status_code(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
        status_code: u16,
    ) -> TestCase<'a> {
        TestCase::new(
            method,
            path,
            TestCaseResult::Failure {
                kind: FailureKind::UnexpectedStatusCode { status_code },
            },
        )
    }
    pub fn response_conformance(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
    ) -> TestCase<'a> {
        TestCase::new(
            method,
            path,
            TestCaseResult::Failure {
                kind: FailureKind::ResponseConformance,
            },
        )
    }
}

// Output idea:
// [{"result": "PASS"}, {"result": "FAILURE", "kind": "UNEXPECTED_STATUS_CODE",
// "response_status_code": 403}]
