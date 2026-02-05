use std::fs::{File, create_dir_all};
use std::io::{BufWriter, Write};
use std::path::Path;
use chrono::Datelike;
use crate::core::Game;
use crate::core::game_settings::GameSettings;

// Configuration constants
const WRITE_FILES_TO_ABSOLUTE_PATH: bool = false;
const INSTALLED_BASE_PATH: &str = "";
const MONTH_ABBRS: &[&str] = &["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];

/// High-level save function that orchestrates the save process
pub fn save_game(game: &std::sync::Arc<Game>, force_save: bool) -> Result<(), Box<dyn std::error::Error>> {
    let settings = game.settings.borrow();

    // Check if save is necessary
    if settings.level.is_empty() || (!force_save && !settings.modified) {
        return Ok(());
    }

    let level = settings.level.clone();
    drop(settings); // Release the borrow before proceeding

    let file_name = generate_file_name(&level, WRITE_FILES_TO_ABSOLUTE_PATH);
    let file_contents = generate_file_contents(game)?;
    save_file_contents(&file_name, &file_contents)?;

    // Mark game as saved
    game.settings.borrow_mut().modified = false;

    println!("Saved discovered game state to file: {}", file_name);
    Ok(())
}

/// Returns the base path for saving files
fn get_base_path(absolute_path: bool) -> String {
    if absolute_path {
        INSTALLED_BASE_PATH.to_string()
    } else {
        String::new()
    }
}

/// Converts a level name to an annualized format (adds year for daily puzzles)
fn annualize_daily_puzzle_file_name(level_num: &str) -> String {
    let level_lower = level_num.to_lowercase();
    if level_lower.len() >= 3 {
        let prefix = &level_lower[0..3];
        if MONTH_ABBRS.contains(&prefix) {
            let year = chrono::Local::now().year();
            return format!("{}/{}", year, level_num);
        }
    }
    level_num.to_string()
}

/// Generates the full file path for a given level
fn generate_file_name(level_num: &str, absolute_path: bool) -> String {
    let base_path = get_base_path(absolute_path);
    let annualized_name = annualize_daily_puzzle_file_name(level_num);

    if base_path.is_empty() {
        format!("wslevels/{}.txt", annualized_name)
    } else {
        format!("{}/wslevels/{}.txt", base_path, annualized_name)
    }
}

/// Generates the file contents as a string
fn generate_file_contents(game: &std::sync::Arc<Game>) -> Result<String, Box<dyn std::error::Error>> {
    let mut lines = Vec::new();

    lines.push("i".to_string());

    let settings = game.settings.borrow();
    let special_modes = get_special_modes(&settings);

    let mut level_line = settings.level.clone();
    if !special_modes.is_empty() {
        level_line.push(' ');
        level_line.push_str(&special_modes.join(" "));
    }
    lines.push(level_line);

    lines.push(game.num_vials().to_string());

    // Add vial contents
    if let Some(original_vials) = &settings.original_vials {
        for vial in original_vials {
            lines.push(vial.join("\t"));
        }
    }

    Ok(lines.join("\n"))
}

/// Writes file contents to disk, creating directories as needed
fn save_file_contents(file_name: &str, contents: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Ensure parent directories exist
    let path = Path::new(file_name);
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            create_dir_all(parent)?;
        }
    }

    let file = File::create(file_name)?;
    let mut writer = BufWriter::new(file);
    writeln!(&mut writer, "{}", contents)?;
    writer.flush()?;

    Ok(())
}

/// Helper function to get special modes from game settings
fn get_special_modes(settings: &GameSettings) -> Vec<&'static str> {
    let mut modes = Vec::new();

    if settings.drain_mode {
        modes.push("drain");
    }
    if settings.blind_mode {
        modes.push("blind");
    }
    if settings.had_mystery_spaces {
        modes.push("mystery");
    }

    modes
}
