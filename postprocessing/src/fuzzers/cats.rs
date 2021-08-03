use std::{fs, fs::DirEntry, path::Path};

use globset::{Glob, GlobMatcher};
use rayon::prelude::*;
use regex::Regex;
use serde_json::Value;

use crate::{
    error::ProcessingError,
    output::{ErrorKind, SkipKind, TestCase},
};

lazy_static::lazy_static! {
    static ref FAILED_FUZZER_RE: Regex = Regex::new(r"Fuzzer \[.+?\] failed due to").expect("A valid regex");
    static ref PASSED_CASE_RE: Regex = Regex::new(r"Call returned as expected\. Response code [0-9]+ matches the contract\. Response body matches the contract!").expect("A valid regex");
    static ref TEST_FILE_GLOB: GlobMatcher = Glob::new(r"**/Test*.js").expect("Valid pattern").compile_matcher();
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
    // OWASP recommendations
    "UnsupportedAcceptHeadersFuzzer",
    "DummyAcceptHeadersFuzzer",
    "DummyContentTypeHeadersFuzzer",
    "UnsupportedTypeHeadersFuzzer",
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
    "NullValuesInFieldsFuzzer",
    "RemoveFieldsFuzzer",
    "DecimalValuesInIntegerFieldsFuzzer",
    "BooleanFieldsFuzzer",
    // Always expect 400, 413, 414, 422 codes
    // Data itself may be valid or there could be 404
    "StringFieldsLeftBoundaryFuzzer",
    "StringFieldsRightBoundaryFuzzer",
    "StringFormatTotallyWrongValuesFuzzer",
    "ExtremeNegativeValueIntegerFieldsFuzzer",
    "ExtremePositiveValueInIntegerFieldsFuzzer",
    "StringsInNumericFieldsFuzzer",
    "BypassAuthenticationFuzzer",
    "VeryLargeStringsFuzzer",
    "InvalidValuesInEnumsFieldsFuzzer",
    "IntegerFieldsLeftBoundaryFuzzer",
    "IntegerFieldsRightBoundaryFuzzer",
    "DecimalFieldsLeftBoundaryFuzzer",
    "DecimalFieldsRightBoundaryFuzzer",
    "ExtremePositiveValueDecimalFieldsFuzzer",
    "ExtremeNegativeValueDecimalFieldsFuzzer",
];

fn is_not_universal(fuzzer_name: &str) -> bool {
    NOT_UNIVERSAL_FUZZERS.contains(&fuzzer_name)
}

static IGNORED_FUZZERS: &[&str] = &[
    // We run tests per endpoint
    "HttpMethodsFuzzer",
];
/// Whether it is a fuzzer's failure.
fn is_fuzzer_failure(case: &str) -> bool {
    FAILED_FUZZER_RE.is_match(case)
}

/// Is this fuzzer ignored?
fn is_ignored_fuzzer(case: &str) -> bool {
    IGNORED_FUZZERS.iter().any(|f| case.contains(f))
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

pub(crate) fn process_files(directory: &Path) -> impl Iterator<Item = TestCase> {
    let paths: Vec<_> = fs::read_dir(directory)
        .expect("Can't read directory")
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
    let cases: Vec<_> = paths.into_par_iter().map(process_file).collect();
    cases.into_iter()
}

fn process_file(entry: DirEntry) -> TestCase<'static> {
    let data = read_json(&entry).expect("Failed to read JSON");
    let fuzzer = data["fuzzer"].as_str().expect("Always a string");
    let details = data["resultDetails"].as_str().expect("Always a string");
    if is_fuzzer_failure(details) {
        let path: Option<std::borrow::Cow<'_, str>> = None;
        let method: Option<std::borrow::Cow<'_, str>> = None;
        return TestCase::error(path, method, ErrorKind::Internal);
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
    if (500..600).contains(&status_code) {
        TestCase::server_error(method.to_owned(), path.to_owned(), status_code)
    } else if is_recommendation(fuzzer) {
        TestCase::recommendation(method.to_owned(), path.to_owned(), fuzzer.to_owned())
    } else if is_ignored_fuzzer(fuzzer) {
        TestCase::skip(
            method.to_owned(),
            path.to_owned(),
            SkipKind::NotInteresting,
            fuzzer.to_owned(),
        )
    } else if is_not_universal(fuzzer) {
        // Can not be applied universally to all cases
        TestCase::skip(
            method.to_owned(),
            path.to_owned(),
            SkipKind::InvalidAssumption,
            fuzzer.to_owned(),
        )
    } else if is_passed(details) {
        // There are few cases:
        //  - Response matches the contract defined in the schema
        //  - Failure is expected
        TestCase::pass(method.to_owned(), path.to_owned())
    } else if is_unexpected_response_status(details) {
        // The response status code is not documented
        TestCase::unexpected_status_code(method.to_owned(), path.to_owned(), status_code)
    } else if is_response_conformance_error(details) {
        // Response body does not match the contract
        TestCase::response_conformance(method.to_owned(), path.to_owned())
    } else {
        unreachable!("Unknown test case")
    }
}

fn read_json(entry: &DirEntry) -> Result<Value, ProcessingError> {
    let content = fs::read_to_string(entry.path())?;
    let json_start_idx = content.find('{').expect("Always present");
    serde_json::from_str(&content[json_start_idx..]).map_err(ProcessingError::Json)
}
