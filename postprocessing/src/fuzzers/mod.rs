pub mod api_fuzzer;
use core::fmt;
use std::str::FromStr;

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
}

impl fmt::Display for SchemathesisKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SchemathesisKind::Default => f.write_str("Default"),
            SchemathesisKind::AllChecks => f.write_str("AllChecks"),
            SchemathesisKind::Negative => f.write_str("Negative"),
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
