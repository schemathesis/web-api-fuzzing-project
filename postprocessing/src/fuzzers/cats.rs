use std::fs;
use std::fs::DirEntry;
use std::path::Path;

use globset::{Glob, GlobMatcher};
use rayon::prelude::*;
use regex::Regex;
use serde_json::Value;

use crate::{error::ProcessingError, output::TestCase};

static TEST_CASE_SEPARATOR: &str = "------------------------------------------------------------------------------------------------------------------------------------------------------";

lazy_static::lazy_static! {
    static ref PATH_CASES_RE: Regex = Regex::new(r"Start fuzzing path ").expect("A valid regex");
    static ref UNEXPECTED_RESPONSE_CODE_RE: Regex = Regex::new(r"Call returned as expected, but with undocumented code: expected \[[0-9 ,]+\], actual \[([0-9]+)\]\.").expect("A valid regex");
    static ref METHOD_RE: Regex = Regex::new(r"Protocol: HTTP/[0-9]\.[0-9], Method: ([A-Z]+), ReasonPhrase").expect("A valid regex");
    static ref FAILED_FUZZER_RE: Regex = Regex::new(r"Fuzzer \[.+?\] failed due to").expect("A valid regex");
    static ref PASSED_CASE_RE: Regex = Regex::new(r"Call returned as expected\. Response code [0-9]+ matches the contract\. Response body matches the contract!").expect("A valid regex");
    static ref TEST_FILE_RE: Regex = Regex::new(r"Test[0-9]+\.js").expect("A valid regex");
    static ref TEST_FILE_GLOB: GlobMatcher = Glob::new(r"**/Test*.js").expect("Valid pattern").compile_matcher();
}

pub fn process_stdout(content: &str) {
    // The first block contains general info about Cats, skip it.
    for block in PATH_CASES_RE.split(content).skip(1) {
        let path = extract_path(block);
        let cases: Vec<&str> = block.split(TEST_CASE_SEPARATOR).collect();
        for (idx, case) in cases.iter().enumerate() {
            if idx + 1 == cases.len()
                || is_skipped(case)
                || is_fuzzer_failure(case)
                || is_ignored_fuzzer(case)
                || is_ignored_result(case)
            {
                continue;
            }
            let method = METHOD_RE
                .captures(case)
                .expect("Always present")
                .get(1)
                .expect("Always present")
                .as_str();
            if let Some(captures) = UNEXPECTED_RESPONSE_CODE_RE.captures(case) {
                let status_code = captures
                    .get(1)
                    .expect("Always present")
                    .as_str()
                    .parse::<u16>()
                    .expect("Valid status code");
                let tc = TestCase::unexpected_status_code(method, path, status_code);
                println!("test case: {:?}", tc);
            } else if is_response_conformance_error(case) {
                let tc = TestCase::response_conformance(method, path);
                println!("{:?}", tc);
            } else if is_passed(case) {
                let tc = TestCase::pass(method, path);
            } else {
                println!("{}", case)
            }
        }
    }
}

/// Get the currently tested path.
fn extract_path(block: &str) -> &str {
    let line_end_idx = block.find("\n").expect("There is always a line end");
    &block[..line_end_idx - 1]
}

/// Whether a test case was skipped by the fuzzer.
fn is_skipped(case: &str) -> bool {
    case.contains("Skipped due to:")
}

// These fuzzers only verify recommendations like naming style
// Or presence of some good practices in the API schema
static RECOMMENDATION_FUZZERS: &[&str] = &[
    "NamingsContractInfoFuzzer",
    "PathTagsContractInfoFuzzer",
    "RecommendedHeadersContractInfoFuzzer",
    "TopLevelElementsContractInfoFuzzer",
    "VersionsContractInfoFuzzer",
    // Missing security-related headers
    "CheckSecurityHeadersFuzzer",
    // Path does not accept "application/xml" as Content-Type
    "XmlContentTypeContractInfoFuzzer",
];

fn is_recommendation(fuzzer_name: &str) -> bool {
    RECOMMENDATION_FUZZERS.contains(&fuzzer_name)
}

// These fuzzers do not apply to all situations
// Some of them expect 2xx in any case, but the response itself returns 404 which makes them fail
static NOT_UNIVERSAL_FUZZERS: &[&str] = &[
    // Always expect 2xx codes
    // Data itself might be not correct according to the backend validation rules
    // Or it could be 404 because some object was not found in the DB
    "LeadingSpacesInFieldsTrimValidateFuzzer",
    "TrailingSpacesInFieldsTrimValidateFuzzer",
    "HappyFuzzer",
    "ExtraHeaderFuzzer",
    "NewFieldsFuzzer",
    "EmptyStringValuesInFieldsFuzzer",
    "StringFormatAlmostValidValuesFuzzer",
    "DuplicateHeaderFuzzer",
    "SpacesOnlyInFieldsTrimValidateFuzzer",
    // Always expect 400, 413, 414, 422 codes
    // Data itself may be valid or there could be 404
    "StringFieldsLeftBoundaryFuzzer",
    "StringFieldsRightBoundaryFuzzer",
    "StringFormatTotallyWrongValuesFuzzer",
    "ExtremeNegativeValueIntegerFieldsFuzzer",
    "ExtremePositiveValueInIntegerFieldsFuzzer",
    "StringsInNumericFieldsFuzzer",
    "BypassAuthenticationFuzzer",
];

fn is_not_universal(fuzzer_name: &str) -> bool {
    NOT_UNIVERSAL_FUZZERS.contains(&fuzzer_name)
}

static IGNORED_FUZZERS: &[&str] = &[
    // TODO: Should it be an error?
    "UnsupportedAcceptHeadersFuzzer",
    // May be reasonable, but could be 5xx
    "UnsupportedContentTypesHeadersFuzzer",
    // TODO: If the value is not nullable, then it is similar to negative testing
    "NullValuesInFieldsFuzzer",
    // Not universal - could be 5xx or 2xx
    "DummyRequestFuzzer",
    // Not universal
    // Not universal
    "DummyAcceptHeadersFuzzer",
    // TODO: Seems like negative testing
    "RemoveFieldsFuzzer",
    // Could be 5xx
    "DummyContentTypeHeadersFuzzer",
    // Not universal - could be anything
    "VeryLargeStringsFuzzer",
    // TODO. good point - it should be 405. But 5xx also may occur
    "HttpMethodsFuzzer",
    // TODO: Not universal - could be 404. What in case of 2xx?
    "InvalidValuesInEnumsFieldsFuzzer",
    // Not universal - could be 404
    "ExtremeNegativeValueIntegerFieldsFuzzer",
    "ExtremePositiveValueInIntegerFieldsFuzzer",
    // TODO: is affected by "format"? It is a recommendation
    "IntegerFieldsRightBoundaryFuzzer",
    "IntegerFieldsLeftBoundaryFuzzer",
    // Not universal - could be 404. Also it could be a short-circuit logic - skip all validation
    // if some object is not found
    "StringsInNumericFieldsFuzzer",
    "DecimalValuesInIntegerFieldsFuzzer",
    // Not universal - could be 404
    "BypassAuthenticationFuzzer",
];
/// Whether it is a fuzzer's failure.
fn is_fuzzer_failure(case: &str) -> bool {
    FAILED_FUZZER_RE.is_match(case)
}

/// Is this fuzzer ignored?
fn is_ignored_fuzzer(case: &str) -> bool {
    IGNORED_FUZZERS.iter().any(|f| case.contains(f))
}

fn is_ignored_result(case: &str) -> bool {
    case.contains("Call returned an unexpected result, but with documented code: expected")
}

fn is_passed(case: &str) -> bool {
    case.contains("Request failed as expected for http method") || PASSED_CASE_RE.is_match(case)
}

fn is_response_conformance_error(string: &str) -> bool {
    string.contains("Response body does NOT match the contract!")
}
fn is_unexpected_response_status(string: &str) -> bool {
    string.contains("Call returned as expected, but with undocumented code")
}

pub(crate) fn process_files(directory: &Path) -> Result<(), ProcessingError> {
    let paths: Vec<_> = fs::read_dir(directory)?
        .filter_map(|entry| {
            if let Ok(entry) = entry {
                if TEST_FILE_GLOB.is_match(entry.path()) {
                    Some(entry)
                } else {
                    None
                }
            } else {
                None
            }
        })
        .collect();
    let cases: Vec<Result<_, ProcessingError>> = paths.par_iter().map(process_file).collect();
    Ok(())
}

fn process_file(entry: &DirEntry) -> Result<Option<TestCase>, ProcessingError> {
    let data = read_json(entry)?;
    let fuzzer = data["fuzzer"].as_str().expect("Always a string");
    let details = data["resultDetails"].as_str().expect("Always a string");
    if is_fuzzer_failure(details) {
        // TODO. return `error`
        return Ok(None);
    }
    let path = data["path"].as_str().expect("Always a string");
    let method = data["response"]["httpMethod"]
        .as_str()
        .expect("Always present");
    let status_code = data["response"]["responseCode"]
        .as_u64()
        .expect("Always present") as u16;
    // Any 5xx response is treated as the "ServerError" case
    // Many built-in fuzzers fails due to their expectations for 2xx or 4xx, but
    // 5xx is not specifically reported. Sometimes 5xx is specified in the schema
    // then the test is passed.
    if status_code >= 500 && status_code < 600 {
        return Ok(Some(TestCase::server_error(
            method.to_owned(),
            path.to_owned(),
            status_code,
        )));
    }
    if is_recommendation(fuzzer) {
        // Not interesting at the research scope
        return Ok(None);
    }
    if is_passed(details) {
        // There are few cases:
        //  - Response matches the contract defined in the schema
        //  - Failure is expected
        return Ok(Some(TestCase::pass(method.to_owned(), path.to_owned())));
    }
    if is_unexpected_response_status(details) {
        // The response status code is not documented
        return Ok(Some(TestCase::unexpected_status_code(
            method.to_owned(),
            path.to_owned(),
            status_code,
        )));
    }
    if is_response_conformance_error(details) {
        // Response body does not match the contract
        return Ok(Some(TestCase::response_conformance(
            method.to_owned(),
            path.to_owned(),
        )));
    }
    if is_not_universal(fuzzer) {
        // These failures can't be applied universally
        return Ok(None);
    }
    // if status_code == 404 {
    // Some fuzzers expect 2xx in all cases,
    //    return Ok(None)
    //}
    // if fuzzer == "InvalidValuesInEnumsFieldsFuzzer" {
    //     println!("{:?}", data)
    // }
    // if is_ignored_result(details) || is_ignored_fuzzer(fuzzer) {
    //     return Ok(None);
    // }

    // TODO. should not be possible
    //unreachable!("Unknown test case")
    Ok(Some(TestCase::pass(method.to_owned(), path.to_owned())))
}

fn read_json(entry: &DirEntry) -> Result<Value, ProcessingError> {
    let content = fs::read_to_string(entry.path())?;
    let json_start_idx = content.find('{').expect("Always present");
    serde_json::from_str(&content[json_start_idx..]).map_err(ProcessingError::Json)
}
