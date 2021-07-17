use glob::glob;
use rayon::prelude::*;
use serde_json::Value;
use std::collections::HashMap;
use std::fs::{create_dir, File};
use std::io::BufReader;
use std::path::{Path, PathBuf};
use structopt::StructOpt;

#[derive(StructOpt, Debug)]
#[structopt(name = "sentry_events")]
struct Opt {
    /// Artifacts directory
    #[structopt(name = "DIRECTORY", parse(from_os_str))]
    directory: PathBuf,

    /// Sentry instance URL
    #[structopt(short, long)]
    url: String,

    /// Sentry API token
    #[structopt(short, long)]
    token: String,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let opt = Opt::from_args();
    let pattern = format!(
        "{}/**/metadata.json",
        &opt.directory.to_str().expect("Valid directory")
    );
    let paths: Vec<_> = glob(&pattern)
        .expect("Invalid pattern")
        .collect::<Result<Vec<_>, _>>()
        .expect("Error during reading directories");

    let paths: Vec<(String, &Path, String)> = paths.par_iter().map(|p| load_metadata(&p)).collect();
    let mut map = HashMap::new();
    for (target, path, run_id) in &paths {
        let runs = map
            .entry(target.to_string())
            .or_insert_with(|| HashMap::with_capacity(30));
        runs.insert(
            run_id.to_owned(),
            path.parent().expect("Has parent dir").to_path_buf(),
        );
    }

    let Opt { url, token, .. } = opt;

    map.par_iter()
        .for_each(|(target, runs)| load_events(&url, &token, target, runs));
    Ok(())
}

fn load_metadata(path: &Path) -> (String, &Path, String) {
    let file = File::open(path).expect("Can't read file");
    let reader = BufReader::new(file);
    let data: Value = serde_json::from_reader(reader).expect("Can't read metadata");
    let target = data["target"]
        .as_str()
        .expect("`run_id` should be a string");
    let run_id = data["run_id"]
        .as_str()
        .expect("`run_id` should be a string");
    (target.to_string(), path, run_id.to_string())
}

fn load_events(url: &str, token: &str, target: &str, runs: &HashMap<String, PathBuf>) {
    println!("Loading: {}", target);
    let client = reqwest::blocking::Client::new();
    if let (Some(mut next), true) = make_call(
        &client,
        &format!("{}api/0/projects/sentry/{}/events/?full=true", url, target),
        token,
        runs,
    ) {
        while let (Some(nxt), true) = make_call(&client, &next, token, runs) {
            next = nxt;
        }
    }
}

fn make_call(
    client: &reqwest::blocking::Client,
    url: &str,
    token: &str,
    runs: &HashMap<String, PathBuf>,
) -> (Option<String>, bool) {
    let response = client
        .get(url)
        .bearer_auth(token)
        .send()
        .expect("Valid response");
    if response.status() == 404 {
        return (None, false);
    }
    let link_header = response
        .headers()
        .get(reqwest::header::LINK)
        .expect("Link header");
    let links =
        parse_link_header::parse(link_header.to_str().expect("valid string")).expect("Valid links");
    let events: Value = response.json().expect("Valid json");
    if let Some(events) = events.as_array() {
        for event in events {
            for tag in event["tags"].as_array().expect("Array") {
                if let Some("wafp.run-id") = tag["key"].as_str() {
                    let run_id = tag["value"].as_str().expect("String");
                    if let Some(run_directory) = runs.get(run_id) {
                        let output_directory = run_directory.join("sentry_events");
                        let _ = create_dir(&output_directory);
                        let event_id = event["id"].as_str().expect("Event ID is a string");
                        let output_path = output_directory.join(format!("{}.json", event_id));
                        let output_file = File::create(output_path).expect("Can't create a file");
                        serde_json::to_writer(&output_file, &event).expect("Can't serialize event");
                    }
                }
            }
        }
    }
    match links.get(&Some("next".to_string())) {
        Some(parse_link_header::Link {
            raw_uri, params, ..
        }) => {
            let results = match params.get("results").expect("Present").as_str() {
                "true" => true,
                "false" => false,
                value => panic!("Unknown value for `results`: {}", value),
            };
            (Some(raw_uri.to_string()), results)
        }
        None => (None, false),
    }
}
