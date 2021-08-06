use crate::targets::Failure;
use core::str::Lines;

pub(crate) fn process_stdout(content: &str) -> Vec<Failure> {
    let total = content
        .matches("Completed 500 Internal Server Error")
        .count();
    let mut failures = Vec::with_capacity(total);
    let mut lines = content.lines();
    while let Some(line) = lines.next() {
        if !line.starts_with("web_1  |") {
            continue;
        }
        let cleaned_line = line[39..].trim();
        if cleaned_line.starts_with("ActiveRecord::RecordNotFound") {
            failures.push(Failure {
                method: Some("POST".to_string()),
                path: Some("/api/graphql".to_string()),
                title: "ActiveRecord::RecordNotFound".to_string(),
                traceback: collect_traceback(&mut lines),
            })
        } else if cleaned_line.starts_with("ArgumentError") {
            failures.push(Failure {
                method: Some("POST".to_string()),
                path: Some("/api/graphql".to_string()),
                title: "ArgumentError".to_string(),
                traceback: collect_traceback(&mut lines),
            })
        }
    }
    assert_eq!(failures.len(), total);
    failures
}

fn collect_traceback(lines: &mut Lines) -> String {
    let mut traceback = String::with_capacity(4096);
    for line in lines {
        if !line.starts_with("web_1  |") {
            continue;
        }
        let cleaned = line[39..].trim();
        if cleaned.is_empty() {
            break;
        } else {
            traceback.push_str(cleaned);
            traceback.push('\n')
        }
    }
    traceback
}
