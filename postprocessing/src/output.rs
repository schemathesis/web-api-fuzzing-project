use std::borrow::Cow;

#[derive(Debug)]
pub enum TestCaseResult {
    Pass,
    Failure(FailureKind),
    Error,
}
#[derive(Debug)]
pub enum FailureKind {
    UnexpectedStatusCode(u16),
    ResponseConformance,
}

#[derive(Debug)]
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
    pub fn unexpected_status_code(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
        status_code: u16,
    ) -> TestCase<'a> {
        TestCase::new(
            method,
            path,
            TestCaseResult::Failure(FailureKind::UnexpectedStatusCode(status_code)),
        )
    }
    pub fn response_conformance(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
    ) -> TestCase<'a> {
        TestCase::new(
            method,
            path,
            TestCaseResult::Failure(FailureKind::ResponseConformance),
        )
    }
}

// Output idea:
// [{"result": "PASS"}, {"result": "FAILURE", "kind": "UNEXPECTED_STATUS_CODE",
// "response_status_code": 403}]
