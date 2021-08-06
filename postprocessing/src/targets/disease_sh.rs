use crate::targets::Failure;
use core::str::Lines;
use regex::Regex;
use std::collections::VecDeque;

lazy_static::lazy_static! {
    static ref FAILURE_RE: Regex = Regex::new(r"Z \w+Error").expect("Valid regex");
    static ref URL_RE: Regex = Regex::new(r"URL: (.+)").expect("Valid regex");
}

pub(crate) fn process_stdout(content: &str) -> Vec<Failure> {
    let mut failures = Vec::new();
    let mut lines = content.lines();
    let mut last_lines = VecDeque::with_capacity(20);
    while let Some(line) = lines.next() {
        last_lines.push_front(line);
        last_lines.truncate(20);
        if !FAILURE_RE.is_match(line) {
            continue;
        }
        let cleaned_line = line[41..].trim();
        if cleaned_line
            .starts_with("ReplyError: ERR wrong number of arguments for 'hexists' command")
        {
            let path = get_request_path(&last_lines);
            failures.push(Failure {
                method: None,
                path,
                title: "ReplyError: ERR wrong number of arguments for 'hexists' command"
                    .to_string(),
                traceback: collect_traceback(&mut lines),
            })
        } else if cleaned_line.starts_with("RangeError: Invalid time value") {
            let path = get_request_path(&last_lines);
            failures.push(Failure {
                method: None,
                path,
                title: "RangeError: Invalid time value".to_string(),
                traceback: collect_traceback(&mut lines),
            })
        } else if cleaned_line.starts_with("URIError: Failed to decode param") {
            continue;
        } else {
            panic!("Unknown failure: {}", cleaned_line)
        }
    }
    failures
}

fn get_request_path(lines: &VecDeque<&str>) -> Option<String> {
    let mut path = None;
    for line in lines.iter() {
        if let Some(captures) = URL_RE.captures(line) {
            path = Some(
                captures
                    .get(1)
                    .expect("Always present")
                    .as_str()
                    .to_string(),
            );
            break;
        }
    }
    path
}

fn collect_traceback(lines: &mut Lines) -> String {
    let mut traceback = String::with_capacity(512);
    for line in lines {
        if !line.starts_with("web_1  ") {
            continue;
        }
        let cleaned = line[41..].trim().trim_end_matches("{").trim();
        if !cleaned.starts_with("at ") {
            break;
        } else {
            traceback.push_str(cleaned);
            traceback.push('\n')
        }
    }
    traceback
}
