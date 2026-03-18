use chrono::{Datelike, Local};
use std::path::PathBuf;

use crate::io::constants::{INSTALLED_BASE_PATH, LEVEL_DIR, LEVEL_EXT, MONTH_ABBRS};

/// Returns the base path for saving files
fn get_base_path(absolute_path: bool) -> PathBuf {
    if absolute_path {
        PathBuf::from(INSTALLED_BASE_PATH)
    } else {
        PathBuf::new()
    }
}

/// Converts a level name to an annualized format (adds year for daily puzzles)
fn include_path_to_level(path: &mut PathBuf, level_num: &str) {
    let level_lower = level_num.to_lowercase();
    if level_lower.len() >= 3 && MONTH_ABBRS.contains(&&level_lower[0..3]) {
        path.push(Local::now().year().to_string());
    }
    path.push(level_num);
}

/// Generates the full file path for a given level
pub fn generate_file_name(level_num: &str, absolute_path: bool) -> String {
    let mut path = get_base_path(absolute_path);
    path.push(LEVEL_DIR);
    include_path_to_level(&mut path, level_num);
    path.set_extension(LEVEL_EXT);
    path.to_str().unwrap().to_string()
}
