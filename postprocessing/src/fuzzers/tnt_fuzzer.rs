use crate::output::TestCase;
use url::Url;

const RED: &str = "\x1b[31m";
const GREEN: &str = "\x1b[32";
const SUFFIX: &str = "\x1b[0m";

pub fn process_stdout(content: &str) -> impl Iterator<Item = TestCase> {
    let (_, table) = content
        .split_once("Fetching open API from: ")
        .expect("Should always be there");
    table.lines().skip(1).map(process_row)
}

fn process_row(row: &str) -> TestCase {
    let mut cells = row.split('|');
    let method =
        strip_color(cells.next().expect("Always present"), RED, SUFFIX).to_ascii_uppercase();
    let url = strip_color(cells.next().expect("Always present"), GREEN, SUFFIX);
    let path = Url::parse(url).expect("Invalid URL").path().to_owned();
    cells.next(); // Skip empty column '|-|'
    let status_code = cells
        .next()
        .expect("Always there")
        .trim()
        .parse::<u16>()
        .expect("Valid status code");
    let reason = cells.next().expect("Always present").trim();
    if reason == "None" {
        // When "documented_reason" is stringified Python's `None`
        // it means that this response code is not documented
        TestCase::unexpected_status_code(method, path, status_code)
    } else if (500..600).contains(&status_code) {
        // Server error
        TestCase::server_error(method, path, status_code)
    } else {
        // Otherwise it is documented
        TestCase::pass(method, path)
    }
}

fn strip_color<'a>(value: &'a str, prefix: &str, suffix: &str) -> &'a str {
    value
        .trim()
        .strip_prefix(prefix)
        .expect("Color code is always present")
        .strip_suffix(suffix)
        .expect("Color code is always present")
        .trim()
}
