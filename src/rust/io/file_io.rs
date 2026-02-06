use crate::core::{Game, GameSettings};
use crate::io::constants::*;
use crate::io::path::generate_file_name;
use std::fs::{File, create_dir_all};
use std::io::Write;
use std::path::Path;

/// High-level save function that orchestrates the save process
pub fn save_game(game: &Game, force_save: bool) -> Result<(), Box<dyn std::error::Error>> {
    let level: String;
    {
        // Limit the scope of mutable settings so later calls can use `settings`
        let settings = game.settings.borrow();

        // Check if save is necessary
        if settings.level.is_empty() || (!force_save && !settings.modified) {
            return Ok(());
        }

        level = settings.level.clone();
    }

    let file_name = generate_file_name(&level, WRITE_FILES_TO_ABSOLUTE_PATH);
    save_game_to_file(game, &file_name)?;

    game.settings.borrow_mut().modified = false;
    Ok(())
}

pub fn save_game_to_file(game: &Game, file_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    let file_contents = generate_file_contents(game)?;
    save_file_contents(&file_name, &file_contents)?;

    // Mark game as saved
    println!("Saved game state to file: {}", file_name);

    Ok(())
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
        create_dir_all(parent)?;
    }

    let mut file = File::create(file_name)?;
    writeln!(&mut file, "{}", contents)?;

    Ok(())
}

/// Helper function to get special modes from game settings
fn get_special_modes(settings: &GameSettings) -> Vec<&'static str> {
    let mut modes = Vec::new();

    if settings.drain_mode {
        modes.push(DRAIN_MODE_FLAG);
    }
    if settings.blind_mode {
        modes.push(BLIND_MODE_FLAG);
    }
    if settings.had_mystery_spaces {
        modes.push(MYSTERY_MODE_FLAG);
    }

    modes
}
