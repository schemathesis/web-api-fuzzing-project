use crate::output::{ErrorKind, FailureKind, TestCase, TestCaseResult};
use regex::Regex;
use url::Url;

lazy_static::lazy_static! {
    static ref CURL_RE: Regex = Regex::new(r"Curl command: curl -i -X (\w+) .+ '(http://.+)'").expect("Valid regex");
}

pub fn process_stdout(content: &str) -> impl Iterator<Item = TestCase> {
    content
        .split("Falsifying example:")
        .skip(1)
        .map(process_case)
}

fn process_case(case: &str) -> TestCase {
    let (method, path) = if let Some(captures) = CURL_RE.captures(case) {
        let method = captures.get(1).expect("Should always match").as_str();
        let url = captures.get(2).expect("Should always match").as_str();
        let parsed = Url::parse(url).expect("A valid URL");
        let path = parsed.path().to_owned();
        (Some(method.to_owned()), Some(path))
    } else {
        (None, None)
    };
    if case.contains("AssertionError: Response content-type") {
        TestCase::new(
            method,
            path,
            TestCaseResult::Failure {
                kind: FailureKind::ContentTypeConformance,
            },
        )
    } else if case.contains("Exception: ('Invalid',") {
        TestCase::error(method, path, ErrorKind::Schema)
    } else {
        panic!("Unknown case")
    }
}
