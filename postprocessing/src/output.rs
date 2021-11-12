use std::borrow::Cow;

#[derive(Debug, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "type")]
pub enum TestCaseResult {
    Pass,
    Skip { kind: SkipKind, reason: String },
    Recommendation { kind: String },
    Failure { kind: FailureKind },
    Error { kind: ErrorKind },
}
#[derive(Debug, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "type")]
pub enum FailureKind {
    ServerError { status_code: u16 },
    UnexpectedStatusCode { status_code: u16 },
    ResponseConformance,
    ResponseHeadersConformance,
    ContentTypeConformance,
    RequestTimeout,
    MissingContentType,
    MalformedMediaType,
}
#[derive(Debug, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "type")]
pub enum ErrorKind {
    // Can not reliably reproduce the failure.
    Flaky,
    Unsatisfiable,
    // Schema is not valid.
    Schema,
    Internal,
}
#[derive(Debug, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "type")]
pub enum SkipKind {
    // Some assumption imposed by the fuzzer is not valid.
    InvalidAssumption,
    // Fuzzer can not test an endpoint.
    CanNotTest,
    // Not interesting in the research scope.
    NotInteresting,
}

#[derive(Debug, serde::Serialize)]
pub struct TestCase<'a> {
    method: Option<Cow<'a, str>>,
    path: Option<Cow<'a, str>>,
    result: TestCaseResult,
}

impl<'a> TestCase<'a> {
    pub fn new(
        method: Option<impl Into<Cow<'a, str>>>,
        path: Option<impl Into<Cow<'a, str>>>,
        result: TestCaseResult,
    ) -> TestCase<'a> {
        TestCase {
            method: method.map(|x| x.into()),
            path: path.map(|x| x.into()),
            result,
        }
    }
    pub fn pass(method: impl Into<Cow<'a, str>>, path: impl Into<Cow<'a, str>>) -> TestCase<'a> {
        TestCase::new(Some(method), Some(path), TestCaseResult::Pass)
    }
    pub fn skip(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
        kind: SkipKind,
        reason: String,
    ) -> TestCase<'a> {
        TestCase::new(
            Some(method),
            Some(path),
            TestCaseResult::Skip { kind, reason },
        )
    }
    pub fn recommendation(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
        kind: String,
    ) -> TestCase<'a> {
        TestCase::new(
            Some(method),
            Some(path),
            TestCaseResult::Recommendation { kind },
        )
    }
    pub fn error(
        method: Option<impl Into<Cow<'a, str>>>,
        path: Option<impl Into<Cow<'a, str>>>,
        kind: ErrorKind,
    ) -> TestCase<'a> {
        TestCase::new(method, path, TestCaseResult::Error { kind })
    }
    pub fn server_error(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
        status_code: u16,
    ) -> TestCase<'a> {
        TestCase::new(
            Some(method),
            Some(path),
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
            Some(method),
            Some(path),
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
            Some(method),
            Some(path),
            TestCaseResult::Failure {
                kind: FailureKind::ResponseConformance,
            },
        )
    }
    pub fn content_type_conformance(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
    ) -> TestCase<'a> {
        TestCase::new(
            Some(method),
            Some(path),
            TestCaseResult::Failure {
                kind: FailureKind::ContentTypeConformance,
            },
        )
    }
    pub fn malformed_media_type(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
    ) -> TestCase<'a> {
        TestCase::new(
            Some(method),
            Some(path),
            TestCaseResult::Failure {
                kind: FailureKind::MalformedMediaType,
            },
        )
    }
    pub fn missing_content_type(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
    ) -> TestCase<'a> {
        TestCase::new(
            Some(method),
            Some(path),
            TestCaseResult::Failure {
                kind: FailureKind::MissingContentType,
            },
        )
    }
    pub fn response_headers_conformance(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
    ) -> TestCase<'a> {
        TestCase::new(
            Some(method),
            Some(path),
            TestCaseResult::Failure {
                kind: FailureKind::ResponseHeadersConformance,
            },
        )
    }
    pub fn request_timeout(
        method: impl Into<Cow<'a, str>>,
        path: impl Into<Cow<'a, str>>,
    ) -> TestCase<'a> {
        TestCase::new(
            Some(method),
            Some(path),
            TestCaseResult::Failure {
                kind: FailureKind::RequestTimeout,
            },
        )
    }
}
