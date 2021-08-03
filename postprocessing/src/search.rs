use crate::{error::ProcessingError, fuzzers};
use globset::{Glob, GlobMatcher};
use std::{
    fs::{read_dir, DirEntry},
    path::Path,
};

pub(crate) fn read_dir_by_glob(
    directory: &Path,
    glob: GlobMatcher,
) -> Result<Vec<DirEntry>, ProcessingError> {
    Ok(read_dir(directory)?
        .filter_map(|entry| {
            if let Ok(entry) = entry {
                if glob.is_match(entry.path()) {
                    Some(entry)
                } else {
                    None
                }
            } else {
                None
            }
        })
        .collect())
}

pub(crate) fn compile_glob(
    directory: &Path,
    fuzzers: &[fuzzers::Fuzzer],
    targets: &[String],
    indices: &[String],
) -> Result<GlobMatcher, ProcessingError> {
    // Glob pattern for collecting all items that are selected for processing
    let pattern = create_pattern(directory, fuzzers, targets, indices)?;
    Ok(Glob::new(&pattern)?.compile_matcher())
}

pub(crate) fn create_pattern(
    directory: &Path,
    fuzzers: &[fuzzers::Fuzzer],
    targets: &[String],
    indices: &[String],
) -> Result<String, ProcessingError> {
    Ok(format!(
        "{}/{}-{}-{}",
        directory
            .to_str()
            .ok_or_else(|| ProcessingError::InvalidDirectoryName(directory.to_path_buf()))?,
        as_pattern(fuzzers),
        as_pattern(targets),
        as_pattern(indices)
    ))
}

/// Convert a slice of items into a glob pattern.
fn as_pattern(items: &[impl ToString]) -> String {
    if items.is_empty() {
        "*".to_string()
    } else if items.len() == 1 {
        items[0].to_string()
    } else {
        let mut pattern = '{'.to_string();
        for (idx, item) in items.iter().enumerate() {
            pattern.push_str(&item.to_string());
            if idx != items.len() - 1 {
                pattern.push(',')
            }
        }
        pattern.push('}');
        pattern
    }
}
