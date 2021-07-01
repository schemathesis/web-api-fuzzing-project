use core::fmt;
use std::{fmt::Debug, path::PathBuf};

#[derive(Debug)]
pub enum ProcessingError {
    Glob(globset::Error),
    InvalidDirectoryName(PathBuf),
    IO(std::io::Error),
    Json(serde_json::Error),
}

impl From<globset::Error> for ProcessingError {
    fn from(e: globset::Error) -> Self {
        ProcessingError::Glob(e)
    }
}

impl From<std::io::Error> for ProcessingError {
    fn from(e: std::io::Error) -> Self {
        ProcessingError::IO(e)
    }
}

impl From<serde_json::Error> for ProcessingError {
    fn from(e: serde_json::Error) -> Self {
        ProcessingError::Json(e)
    }
}

impl fmt::Display for ProcessingError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ProcessingError::Glob(e) => <globset::Error as fmt::Display>::fmt(e, f),
            ProcessingError::InvalidDirectoryName(e) => e.fmt(f),
            ProcessingError::IO(e) => <std::io::Error as fmt::Display>::fmt(e, f),
            ProcessingError::Json(e) => <serde_json::Error as fmt::Display>::fmt(e, f),
        }
    }
}
