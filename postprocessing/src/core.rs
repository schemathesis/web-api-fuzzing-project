use crate::{
    error::ProcessingError,
    fuzzers,
    search::{compile_glob, read_dir_by_glob},
};
use indicatif::ParallelProgressIterator;
use rayon::prelude::*;
use std::{fs, io::BufReader, path::Path, time::Instant};

/// Process raw artifacts.
pub fn process(
    directory: &Path,
    fuzzers: &[fuzzers::Fuzzer],
    targets: &[String],
    indices: &[String],
) -> Result<(), ProcessingError> {
    let start = Instant::now();
    let glob = compile_glob(directory, fuzzers, targets, indices)?;
    let paths = read_dir_by_glob(directory, glob)?;
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

#[derive(Debug, serde::Deserialize)]
struct RunMetadata {
    fuzzer: fuzzers::Fuzzer,
    target: String,
    run_id: Option<String>,
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
