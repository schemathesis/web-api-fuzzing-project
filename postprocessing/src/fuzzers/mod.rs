pub mod api_fuzzer;
pub mod cats;
pub mod fuzz_lightyear;
pub mod got_swag;
pub mod restler;
pub mod schemathesis;
pub mod swagger_fuzzer;
pub mod tnt_fuzzer;
use serde::ser::{SerializeSeq, Serializer};

use crate::{error::ProcessingError, output::TestCase};
use core::fmt;
use std::{
    fs,
    path::{Path, PathBuf},
    str::FromStr,
};

#[derive(Debug)]
pub enum FuzzerError {
    UnknownFuzzer(String),
}

impl fmt::Display for FuzzerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FuzzerError::UnknownFuzzer(name) => f.write_str(&format!("Unknown fuzzer: {}", name)),
        }
    }
}

#[derive(Debug)]
pub enum Fuzzer {
    ApiFuzzer,
    TntFuzzer,
    Schemathesis(SchemathesisKind),
    Restler,
    Cats,
    SwaggerFuzzer,
    GotSwag,
    FuzzLightyear,
}

#[derive(Debug)]
pub enum SchemathesisKind {
    Default,
    AllChecks,
    Negative,
    StatefulOld,
    StatefulNew,
}

impl fmt::Display for SchemathesisKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SchemathesisKind::Default => f.write_str("Default"),
            SchemathesisKind::AllChecks => f.write_str("AllChecks"),
            SchemathesisKind::Negative => f.write_str("Negative"),
            SchemathesisKind::StatefulOld => f.write_str("StatefulOld"),
            SchemathesisKind::StatefulNew => f.write_str("StatefulNew"),
        }
    }
}

/// Deserialize Fuzzer via its FromStr implementation.
impl<'de> serde::Deserialize<'de> for Fuzzer {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        FromStr::from_str(&s).map_err(serde::de::Error::custom)
    }
}

impl FromStr for Fuzzer {
    type Err = FuzzerError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "api_fuzzer" => Ok(Fuzzer::ApiFuzzer),
            "tnt_fuzzer" => Ok(Fuzzer::TntFuzzer),
            "schemathesis:Default" => Ok(Fuzzer::Schemathesis(SchemathesisKind::Default)),
            "schemathesis:AllChecks" => Ok(Fuzzer::Schemathesis(SchemathesisKind::AllChecks)),
            "schemathesis:Negative" => Ok(Fuzzer::Schemathesis(SchemathesisKind::Negative)),
            "schemathesis:StatefulOld" => Ok(Fuzzer::Schemathesis(SchemathesisKind::StatefulOld)),
            "schemathesis:StatefulNew" => Ok(Fuzzer::Schemathesis(SchemathesisKind::StatefulNew)),
            "restler" => Ok(Fuzzer::Restler),
            "cats" => Ok(Fuzzer::Cats),
            "swagger_fuzzer" => Ok(Fuzzer::SwaggerFuzzer),
            "got_swag" => Ok(Fuzzer::GotSwag),
            "fuzz_lightyear" => Ok(Fuzzer::FuzzLightyear),
            _ => Err(Self::Err::UnknownFuzzer(s.to_string())),
        }
    }
}

impl fmt::Display for Fuzzer {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Fuzzer::ApiFuzzer => f.write_str("api_fuzzer"),
            Fuzzer::TntFuzzer => f.write_str("tnt_fuzzer"),
            Fuzzer::Schemathesis(kind) => {
                f.write_str("schemathesis:")?;
                kind.fmt(f)
            }
            Fuzzer::Restler => f.write_str("restler"),
            Fuzzer::Cats => f.write_str("cats"),
            Fuzzer::SwaggerFuzzer => f.write_str("swagger_fuzzer"),
            Fuzzer::GotSwag => f.write_str("got_swag"),
            Fuzzer::FuzzLightyear => f.write_str("fuzz_lightyear"),
        }
    }
}

fn read_stdout(directory: &Path) -> std::io::Result<String> {
    let output_path = directory.join("stdout.txt");
    std::fs::read_to_string(output_path)
}

pub(crate) fn process(
    fuzzer: Fuzzer,
    directory: &Path,
    out_directory: &PathBuf,
) -> Result<(), ProcessingError> {
    match fuzzer {
        Fuzzer::ApiFuzzer => {
            let content = read_stdout(directory)?;
            store_cases(api_fuzzer::process_stdout(&content), out_directory)?;
        }
        Fuzzer::TntFuzzer => {
            let content = read_stdout(directory)?;
            store_cases(tnt_fuzzer::process_stdout(&content), out_directory)?;
        }
        Fuzzer::Schemathesis(kind) => match kind {
            SchemathesisKind::StatefulNew => {
                let content = read_stdout(directory)?;
                store_cases(schemathesis::process_pytest_output(&content), out_directory)?;
            }
            _ => {
                schemathesis::get_deduplicated_results(directory, out_directory);
                store_cases(schemathesis::process_debug_output(directory), out_directory)?;
            }
        },
        Fuzzer::Restler => {
            restler::get_deduplicated_results(directory, out_directory);
            store_cases(restler::process_network_log(directory), out_directory)?;
        }
        Fuzzer::Cats => {
            store_cases(cats::process_files(directory), out_directory)?;
        }
        Fuzzer::SwaggerFuzzer => {
            let content = read_stdout(directory)?;
            store_cases(swagger_fuzzer::process_stdout(&content), out_directory)?;
        }
        Fuzzer::GotSwag => {
            let content = read_stdout(directory)?;
            store_cases(got_swag::process_stdout(&content), out_directory)?;
        }
        Fuzzer::FuzzLightyear => {
            let content = read_stdout(directory)?;
            store_cases(fuzz_lightyear::process_stdout(&content), out_directory)?;
        }
    };
    Ok(())
}

fn store_cases<'a>(
    cases: impl Iterator<Item = TestCase<'a>>,
    directory: &Path,
) -> Result<(), ProcessingError> {
    let output_path = directory.join("fuzzer.json");
    let output_file = fs::File::create(output_path)?;
    let mut ser = serde_json::Serializer::new(output_file);
    let mut seq = ser.serialize_seq(None)?;
    for test_case in cases {
        seq.serialize_element(&test_case)?;
    }
    seq.end()?;
    Ok(())
}
