use crate::error::ProcessingError;
use crate::fuzzers;
use globset::Glob;
use indicatif::ParallelProgressIterator;
use rayon::prelude::*;
use std::fs;
use std::io::BufReader;
use std::path::Path;

/// Process raw artifacts.
pub fn process(
    directory: &Path,
    fuzzers: &[fuzzers::Fuzzer],
    targets: &[String],
    indices: &[String],
) -> Result<(), ProcessingError> {
    // Glob pattern for collecting all items that are selected for processing
    let pattern = format!(
        "{}/{}-{}-{}",
        directory
            .to_str()
            .ok_or_else(|| ProcessingError::InvalidDirectoryName(directory.to_path_buf()))?,
        as_pattern(fuzzers),
        as_pattern(targets),
        as_pattern(indices)
    );
    let glob = Glob::new(&pattern)?.compile_matcher();

    let paths: Vec<_> = fs::read_dir(directory)?
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
        .collect();
    let results: Vec<_> = paths
        .par_iter()
        .progress_count(paths.len() as u64)
        .map(process_entry)
        .collect();
    for result in results {
        if let Err(err) = result {
            eprintln!("Error: {}", err);
        }
    }
    Ok(())
}

#[derive(Debug, serde::Deserialize)]
struct RunMetadata {
    fuzzer: fuzzers::Fuzzer,
    target: String,
    run_id: String,
    duration: f32,
}

/// Handle individual test runs
fn process_entry(entry: &fs::DirEntry) -> Result<(), ProcessingError> {
    let mut path = entry.path();
    path.push("metadata.json");
    let metadata = read_metadata(&path)?;
    // Process fuzzer & target in parallel (potentially)
    let (fuzzer_result, _target_result) = rayon::join(
        || {
            let mut data_path = entry.path();
            data_path.push("fuzzer");
            fuzzers::process(metadata.fuzzer, &data_path)
        },
        || {
            // TODO. implement target processing
        },
    );
    fuzzer_result?;
    Ok(())
}

fn read_metadata(path: &Path) -> Result<RunMetadata, ProcessingError> {
    let file = fs::File::open(path)?;
    let reader = BufReader::new(file);
    serde_json::from_reader(reader).map_err(ProcessingError::Json)
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
