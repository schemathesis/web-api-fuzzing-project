mod disease_sh;
mod gitlab;
use crate::{error::ProcessingError, fuzzers, metadata, search::read_runs};
use indicatif::ParallelProgressIterator;
use rayon::prelude::*;
use std::{fmt, fs, fs::File, path::Path, str::FromStr, time::Instant};

#[derive(Debug)]
pub enum Target {
    AgeOfEmpires2Api(TargetKind),
    CcccatalogApi(TargetKind),
    Covid19JapanWebApi(TargetKind),
    DiseaseSh(TargetKind),
    GitLab(TargetKind),
    HttpBin(TargetKind),
    JupyterServer(TargetKind),
    JupyterHub(TargetKind),
    MailHog(TargetKind),
    OpenFec(TargetKind),
    OpenTopoData(TargetKind),
    OttoParser(TargetKind),
    PslabWebapp(TargetKind),
    Pulpcore(TargetKind),
    RequestBaskets(TargetKind),
    RestlerDemo(TargetKind),
    Worklog(TargetKind),
}

impl fmt::Display for Target {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Target::AgeOfEmpires2Api(kind) => {
                f.write_fmt(format_args!("age_of_empires_2_api:{}", kind))
            }
            Target::CcccatalogApi(kind) => f.write_fmt(format_args!("cccatalog_api:{}", kind)),
            Target::Covid19JapanWebApi(kind) => {
                f.write_fmt(format_args!("covid19_japan_web_api:{}", kind))
            }
            Target::DiseaseSh(kind) => f.write_fmt(format_args!("disease_sh:{}", kind)),
            Target::GitLab(kind) => f.write_fmt(format_args!("gitlab:{}", kind)),
            Target::HttpBin(kind) => f.write_fmt(format_args!("httpbin:{}", kind)),
            Target::JupyterServer(kind) => f.write_fmt(format_args!("jupyter_server:{}", kind)),
            Target::JupyterHub(kind) => f.write_fmt(format_args!("jupyterhub:{}", kind)),
            Target::MailHog(kind) => f.write_fmt(format_args!("mailhog:{}", kind)),
            Target::OpenFec(kind) => f.write_fmt(format_args!("open_fec:{}", kind)),
            Target::OpenTopoData(kind) => f.write_fmt(format_args!("opentopodata:{}", kind)),
            Target::OttoParser(kind) => f.write_fmt(format_args!("otto_parser:{}", kind)),
            Target::PslabWebapp(kind) => f.write_fmt(format_args!("pslab_webapp:{}", kind)),
            Target::Pulpcore(kind) => f.write_fmt(format_args!("pulpcore:{}", kind)),
            Target::RequestBaskets(kind) => f.write_fmt(format_args!("request_baskets:{}", kind)),
            Target::RestlerDemo(kind) => f.write_fmt(format_args!("restler_demo:{}", kind)),
            Target::Worklog(kind) => f.write_fmt(format_args!("worklog:{}", kind)),
        }
    }
}
#[derive(Debug)]
pub enum TargetKind {
    Default,
    Linked,
}

impl fmt::Display for TargetKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TargetKind::Default => f.write_str("Default"),
            TargetKind::Linked => f.write_str("Linked"),
        }
    }
}

/// Deserialize Fuzzer via its FromStr implementation.
impl<'de> serde::Deserialize<'de> for Target {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        FromStr::from_str(&s).map_err(serde::de::Error::custom)
    }
}
#[derive(Debug)]
pub enum TargetError {
    UnknownTarget(String),
}

impl fmt::Display for TargetError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TargetError::UnknownTarget(name) => {
                f.write_fmt(format_args!("Unknown target: {}", name))
            }
        }
    }
}

impl FromStr for TargetKind {
    type Err = TargetError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "Default" => Ok(Self::Default),
            "Linked" => Ok(Self::Linked),
            _ => Err(Self::Err::UnknownTarget(s.to_string())),
        }
    }
}
impl FromStr for Target {
    type Err = TargetError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if let Some((target, kind)) = s.split_once(':') {
            let kind = TargetKind::from_str(kind)?;
            match target {
                "age_of_empires_2_api" => Ok(Target::AgeOfEmpires2Api(kind)),
                "cccatalog_api" => Ok(Target::CcccatalogApi(kind)),
                "covid19_japan_web_api" => Ok(Target::Covid19JapanWebApi(kind)),
                "disease_sh" => Ok(Target::DiseaseSh(kind)),
                "gitlab" => Ok(Target::GitLab(kind)),
                "httpbin" => Ok(Target::HttpBin(kind)),
                "jupyter_server" => Ok(Target::JupyterServer(kind)),
                "jupyterhub" => Ok(Target::JupyterHub(kind)),
                "mailhog" => Ok(Target::MailHog(kind)),
                "open_fec" => Ok(Target::OpenFec(kind)),
                "opentopodata" => Ok(Target::OpenTopoData(kind)),
                "otto_parser" => Ok(Target::OttoParser(kind)),
                "pslab_webapp" => Ok(Target::PslabWebapp(kind)),
                "pulpcore" => Ok(Target::Pulpcore(kind)),
                "request_baskets" => Ok(Target::RequestBaskets(kind)),
                "restler_demo" => Ok(Target::RestlerDemo(kind)),
                "worklog" => Ok(Target::Worklog(kind)),
                _ => Err(Self::Err::UnknownTarget(s.to_string())),
            }
        } else {
            Err(Self::Err::UnknownTarget(s.to_string()))
        }
    }
}

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
        .map(|entry| process_run(entry, out_directory))
        .collect();
    for result in &results {
        if let Err(err) = result {
            eprintln!("Error: {}", err);
        }
    }
    println!(
        "TARGETS: Processed {} runs in {:.3} seconds",
        results.len(),
        Instant::now().duration_since(start).as_secs_f32()
    );
    Ok(())
}

fn read_stdout(entry: &fs::DirEntry) -> std::io::Result<String> {
    let path = entry.path().join("target").join("stdout.txt");
    std::fs::read_to_string(path)
}

#[derive(Debug, serde::Serialize)]
pub(crate) struct Failure {
    method: Option<String>,
    path: Option<String>,
    title: String,
    traceback: String,
}

fn process_run(entry: &fs::DirEntry, out_directory: &Path) -> Result<(), ProcessingError> {
    let mut path = entry.path();
    path.push("metadata.json");
    let metadata = metadata::read_metadata(&path)?;
    match metadata.target {
        Target::DiseaseSh(_) => {
            let stdout = read_stdout(entry).expect("Failed to read stdout.txt");
            let failures = disease_sh::process_stdout(&stdout);
            store_failures(entry, &failures, out_directory)
        }
        Target::GitLab(_) => {
            let stdout = read_stdout(entry).expect("Failed to read stdout.txt");
            let failures = gitlab::process_stdout(&stdout);
            store_failures(entry, &failures, out_directory)
        }
        Target::AgeOfEmpires2Api(_)
        | Target::CcccatalogApi(_)
        | Target::Covid19JapanWebApi(_)
        | Target::HttpBin(_)
        | Target::JupyterServer(_)
        | Target::JupyterHub(_)
        | Target::MailHog(_)
        | Target::OpenFec(_)
        | Target::OpenTopoData(_)
        | Target::OttoParser(_)
        | Target::PslabWebapp(_)
        | Target::Pulpcore(_)
        | Target::RequestBaskets(_)
        | Target::RestlerDemo(_)
        | Target::Worklog(_) => {}
    }
    Ok(())
}

fn store_failures(entry: &fs::DirEntry, failures: &[Failure], out_directory: &Path) {
    let out_directory =
        out_directory.join(entry.path().file_name().expect("Missing directory name"));
    fs::create_dir_all(&out_directory).expect("Failed to create output directory");
    let output_path = out_directory.join("failures.json");
    let output_file = File::create(output_path).expect("Failed to create file");
    serde_json::to_writer(output_file, failures).expect("Failed to serialize failures");
}
