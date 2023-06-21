use crate::{error::ProcessingError, fuzzers, search::read_runs};
use indicatif::ParallelProgressIterator;
use rayon::iter::{IntoParallelRefIterator, ParallelIterator};
use serde_json::Value;
use std::{
    fs::{read_dir, DirEntry, File},
    path::{Path, PathBuf},
    time::Instant,
};
use url::Url;

/// A separate struct for raw Sentry events.
/// A custom `Deserialize` impl might be more efficient
#[derive(Debug, serde::Deserialize)]
struct RawSentryEvent {
    #[serde(rename(deserialize = "eventID"))]
    event_id: String,
    #[serde(rename(deserialize = "groupID"))]
    group_id: String,
    title: String,
    message: String,
    culprit: String,
    tags: Vec<Tag>,
    entries: Vec<Entry>,
    metadata: Metadata,
}

#[derive(Debug, serde::Deserialize)]
struct Tag {
    key: String,
    value: String,
}

#[derive(Debug, serde::Deserialize)]
#[serde(tag = "type")]
#[serde(rename_all(deserialize = "snake_case"))]
enum Entry {
    Exception { data: ExceptionData },
    Request { data: RequestData },
    Message,
    Breadcrumbs,
}

#[derive(Debug, serde::Deserialize)]
struct ExceptionData {
    values: Vec<ExceptionValue>,
}
#[derive(Debug, serde::Deserialize)]
struct RequestData {
    method: Option<String>,
    url: String,
}

#[derive(Debug, serde::Deserialize, serde::Serialize, Clone)]
struct ExceptionValue {
    r#type: String,
    value: Option<String>,
    stacktrace: Option<Stacktrace>,
}

#[derive(Debug, serde::Deserialize, serde::Serialize, Clone)]
struct Stacktrace {
    frames: Vec<Frame>,
}

#[derive(Debug, serde::Deserialize, serde::Serialize, Clone)]
struct Frame {
    #[serde(rename(deserialize = "lineNo"))]
    line_no: Option<usize>,
    #[serde(rename(deserialize = "colNo"))]
    col_no: Option<usize>,
    function: String,
    filename: String,
    #[serde(skip_serializing)]
    // Used in some corner-cases to determine HTTP method
    vars: Value,
}

#[derive(Debug, serde::Deserialize, serde::Serialize)]
#[serde(untagged)]
#[serde(rename_all(deserialize = "snake_case"))]
enum Metadata {
    Error { r#type: String, value: String },
    OnlyTitle { title: String },
}

#[derive(Debug, serde::Serialize)]
struct SentryEvent {
    #[serde(rename(deserialize = "eventID"))]
    event_id: String,
    #[serde(rename(deserialize = "groupID"))]
    group_id: String,
    title: String,
    message: String,
    culprit: String,
    // Tag with the `transaction` key
    transaction: Option<String>,
    // `method` and `path` are extracted from the `entry` object with the `request` type if it is available
    // In some cases they are extracted from the stacktrace & other location
    method: Option<String>,
    path: Option<String>,
    exceptions: Vec<Vec<ExceptionValue>>,
    metadata: Metadata,
}

pub fn parse_events(
    in_directory: &Path,
    out_directory: &Path,
    fuzzers: &[fuzzers::Fuzzer],
    targets: &[String],
    indices: &[String],
) -> Result<(), ProcessingError> {
    let start = Instant::now();
    let paths = read_runs(in_directory, fuzzers, targets, indices)?;
    let total: usize = paths
        .par_iter()
        .progress_count(paths.len() as u64)
        .map(|entry| process_run(entry, out_directory))
        .sum();
    println!(
        "SENTRY: Processed {} events in {:.3} seconds",
        total,
        Instant::now().duration_since(start).as_secs_f32()
    );
    Ok(())
}

fn process_run(entry: &DirEntry, out_directory: &Path) -> usize {
    let sentry_events_dir = entry.path().join("sentry_events");
    if sentry_events_dir.exists() {
        let paths: Vec<_> = read_dir(sentry_events_dir)
            .expect("Failed to read dir")
            .map(|e| e.expect("Invalid entry").path())
            .collect();
        let events: Vec<_> = paths.par_iter().filter_map(process_file).collect();
        let output_path = out_directory
            .join(entry.path().file_name().expect("Missing directory name"))
            .join("sentry.json");
        let output_file = File::create(&output_path).expect("Failed to create file");
        serde_json::to_writer(output_file, &events).expect("Failed to serialize events");
        events.len()
    } else {
        0
    }
}

fn should_be_skipped(event: &RawSentryEvent) -> bool {
    // Some Python projects emit such lines sometimes
    event.title.contains("code 400, message Bad request syntax")
    // Emitted by Tornado on SIGTERM
    || event.title.contains("received signal 15, stopping")
    || event.title.contains("Received signal SIGTERM")
    // Logs from Jupyter
    || event.title.contains("To access the server, open this file in a browser:")
    // Jupyter Server specific log entry
    || event.title == "{"
}

fn process_file(path: &PathBuf) -> Option<SentryEvent> {
    let file = File::open(path).expect("Can not open file");
    let raw_event: Result<RawSentryEvent, _> = serde_json::from_reader(file);
    match raw_event {
        Ok(raw_event) => {
            if should_be_skipped(&raw_event) {
                return None;
            }

            let get_transaction = |tags: &[Tag]| -> Option<String> {
                for tag in tags {
                    if tag.key == "transaction" {
                        return Some(tag.value.clone());
                    }
                }
                None
            };
            let transaction = get_transaction(&raw_event.tags);

            let get_endpoint = |entries: &[Entry]| -> (Option<String>, Option<String>) {
                for entry in entries {
                    match entry {
                        Entry::Request {
                            data: RequestData { method, url },
                        } => {
                            if let Some(method) = method {
                                let path = Url::parse(url).expect("Invalid URL").path().to_owned();
                                return (Some(method.clone()), Some(path));
                            }
                        }
                        Entry::Message | Entry::Breadcrumbs | Entry::Exception { .. } => continue,
                    }
                }
                // It may be a Gunicorn-level error that is logged differently
                if let Some((_, path)) = raw_event.message.split_once("Error handling request ") {
                    for entry in entries {
                        match entry {
                            // The only place where we can get the HTTP method is local variables in one of the
                            // stackframes
                            Entry::Exception {
                                data: ExceptionData { values },
                            } => {
                                for ExceptionValue { stacktrace, .. } in values {
                                    if let Some(Stacktrace { frames }) = stacktrace {
                                        for Frame { vars, .. } in frames {
                                            if let Some(value) =
                                                vars["environ"]["REQUEST_METHOD"].as_str()
                                            {
                                                let method = &value[1..value.len() - 1];
                                                return (
                                                    Some(method.to_owned()),
                                                    Some(path.to_owned()),
                                                );
                                            }
                                        }
                                    }
                                }
                            }
                            Entry::Message | Entry::Breadcrumbs | Entry::Request { .. } => continue,
                        }
                    }
                };
                (None, None)
            };
            let (method, path) = get_endpoint(&raw_event.entries);

            let exceptions = {
                let mut out = Vec::new();
                for entry in &raw_event.entries {
                    match entry {
                        Entry::Exception {
                            data: ExceptionData { values },
                        } => out.push(values.clone()),
                        Entry::Message | Entry::Breadcrumbs | Entry::Request { .. } => continue,
                    }
                }
                out
            };

            Some(SentryEvent {
                event_id: raw_event.event_id,
                group_id: raw_event.group_id,
                title: raw_event.title,
                message: raw_event.message,
                culprit: raw_event.culprit,
                transaction,
                method,
                path,
                exceptions,
                metadata: raw_event.metadata,
            })
        }
        Err(error) => {
            panic!("Invalid file: {:?} ({})", path, error);
        }
    }
}
