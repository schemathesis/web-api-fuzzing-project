use crate::{error::ProcessingError, fuzzers, metadata, search::read_runs};
use indicatif::ParallelProgressIterator;
use rayon::prelude::*;
use std::{fs, path::Path, time::Instant};

/// Process raw artifacts.
pub fn process(
    directory: &Path,
    fuzzers: &[fuzzers::Fuzzer],
    targets: &[String],
    indices: &[String],
) -> Result<(), ProcessingError> {
    let start = Instant::now();
    let paths = read_runs(directory, fuzzers, targets, indices)?;
    let results: Vec<_> = paths
        .par_iter()
        .progress_count(paths.len() as u64)
        .map(process_entry)
        .collect();
    for result in &results {
        if let Err(err) = result {
            eprintln!("Error: {}", err);
        }
    }
    println!(
        "Processed {} runs in {:.3} seconds",
        results.len(),
        Instant::now().duration_since(start).as_secs_f32()
    );
    Ok(())
}

/// Handle individual test runs
fn process_entry(entry: &fs::DirEntry) -> Result<(), ProcessingError> {
    let mut path = entry.path();
    path.push("metadata.json");
    let metadata = metadata::read_metadata(&path)?;
    let data_path = entry.path().join("fuzzer");
    fuzzers::process(metadata.fuzzer, &data_path)?;
    Ok(())
}
