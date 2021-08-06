use crate::{error::ProcessingError, fuzzers, targets};
use std::{fs, io::BufReader, path::Path};

#[derive(Debug, serde::Deserialize)]
pub(crate) struct RunMetadata {
    pub(crate) fuzzer: fuzzers::Fuzzer,
    pub(crate) target: targets::Target,
    pub(crate) run_id: Option<String>,
    pub(crate) duration: f32,
}
pub(crate) fn read_metadata(path: &Path) -> Result<RunMetadata, ProcessingError> {
    let file = fs::File::open(path)?;
    let reader = BufReader::new(file);
    serde_json::from_reader(reader).map_err(ProcessingError::Json)
}
