#[derive(Debug)]
pub enum TestCaseResult {
    Pass,
    Failure(FailureKind),
    Error,
}
#[derive(Debug)]
pub enum FailureKind {
    UnexpectedStatusCode(u16),
}

#[derive(Debug)]
pub struct TestCase<'a> {
    method: &'a str,
    url: &'a str,
    result: TestCaseResult,
}

impl<'a> TestCase<'a> {
    pub fn new(method: &'a str, url: &'a str, result: TestCaseResult) -> TestCase<'a> {
        TestCase {
            method,
            url,
            result,
        }
    }
}
