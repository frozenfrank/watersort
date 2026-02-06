use std::fs::{File, create_dir_all};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use chrono::Datelike;
use crate::core::Game;
use crate::core::game_settings::GameSettings;
use crate::io::constants::*;


/// High-level save function that orchestrates the save process
pub fn save_game(game: &std::sync::Arc<Game>, force_save: bool) -> Result<(), Box<dyn std::error::Error>> {
    let level: String;
    { // Limit the scope of mutable settings so later calls can use settings
        let settings = game.settings.borrow();

        // Check if save is necessary
        if settings.level.is_empty() || (!force_save && !settings.modified) {
            return Ok(());
        }

        level = settings.level.clone();
    }

    let file_name = generate_file_name(&level, WRITE_FILES_TO_ABSOLUTE_PATH);
    let file_contents = generate_file_contents(game)?;
    save_file_contents(&file_name, &file_contents)?;

    // Mark game as saved
    game.settings.borrow_mut().modified = false;
    println!("Saved discovered game state to file: {}", file_name);

    Ok(())
}

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
       path.push(chrono::Local::now().year().to_string());
    }
    path.push(level_num);
}

/// Generates the full file path for a given level
fn generate_file_name(level_num: &str, absolute_path: bool) -> String {
    let mut path = get_base_path(absolute_path);
    path.push(LEVEL_DIR);
    include_path_to_level(&mut path, level_num);
    path.set_extension("txt");
    path.to_str().unwrap().to_string()
}

/// Generates the file contents as a string
fn generate_file_contents(game: &Game) -> Result<String, Box<dyn std::error::Error>> {
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
    // FIXME: Interpret the vials based on the ColorCodes and the Allocator
    // if let Some(original_vials) = &settings.original_vials {
    //     for vial in original_vials {
    //         lines.push(vial.join("\t"));
    //     }
    // }

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
