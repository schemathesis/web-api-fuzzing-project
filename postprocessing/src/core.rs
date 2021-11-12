use crate::{error::ProcessingError, fuzzers, metadata, search::read_runs};
use indicatif::ParallelProgressIterator;
use rayon::prelude::*;
use std::{fs, path::Path, time::Instant};

/// Process raw artifacts.
pub fn process(
    in_directory: &Path,
    out_directory: &Path,
    fuzzers: &[fuzzers::Fuzzer],
    targets: &[String],
    indices: &[String],
) -> Result<(), ProcessingError> {
    let start = Instant::now();
    let paths = read_runs(in_directory, fuzzers, targets, indices)?;
    let results: Vec<_> = paths
        .par_iter()
        .progress_count(paths.len() as u64)
        .map(|entry| process_entry(entry, out_directory))
        .collect();
    for result in &results {
        if let Err(err) = result {
            eprintln!("Error: {}", err);
        }
    }
    println!(
        "FUZZERS: Processed {} runs in {:.3} seconds",
        results.len(),
        Instant::now().duration_since(start).as_secs_f32()
    );
    Ok(())
}

/// Handle individual test runs
fn process_entry(entry: &fs::DirEntry, out_directory: &Path) -> Result<(), ProcessingError> {
    let out_directory =
        out_directory.join(entry.path().file_name().expect("Missing directory name"));
    fs::create_dir_all(&out_directory).expect("Failed to create output directory");
    let metadata_path = entry.path().join("metadata.json");
    let metadata = metadata::read_metadata(&metadata_path)?;
    let data_path = entry.path().join("fuzzer");
    fuzzers::process(metadata.fuzzer, &data_path, &out_directory)?;
    fs::copy(metadata_path, out_directory.join("metadata.json"))?;
    Ok(())
}
