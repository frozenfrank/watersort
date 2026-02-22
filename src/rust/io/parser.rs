use crate::NUM_SPACES_PER_VIAL;
use crate::core::Color;
use crate::core::Game;
use crate::io::constants::*;
use crate::io::path::generate_file_name;
use crate::types::Vial;
use std::error::Error;
use std::fs::File;
use std::io::{BufRead, BufReader};

type ReadFileResult = Result<Game<'static>, Box<dyn Error + 'static>>;

pub fn read_game_level(level: &str) -> ReadFileResult {
    let file_path = generate_file_name(level, false);
    let game = read_game_file(&file_path);
    if let Ok(game) = &game {
        let mut settings = game.settings.borrow_mut();
        settings.level = level.to_string();
    }
    game
}

pub fn read_game_file(path: &str) -> ReadFileResult {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut lines = reader.lines();

    let mode = lines.next().ok_or("No mode line")??;
    if mode != "i" {
        return Err("Unsupported mode".into());
    }

    let level_line: String = lines.next().ok_or("No level line")??;
    let level_parts: Vec<&str> = level_line.split_whitespace().collect();
    let level = level_parts.get(0).cloned().unwrap_or_default();
    let special_modes: Vec<&str> = level_parts[1..].to_vec();

    let num_vials_str = lines.next().ok_or("No num vials line")??;
    let num_vials: usize = num_vials_str.trim().parse()?;

    let mut vials: Vec<Vial> = Vec::new();
    for _ in 0..num_vials {
        let line = lines.next().ok_or("Not enough vial lines")??;
        let spaces: Vec<String> = line.split_whitespace().map(|s| s.to_string()).collect();
        if spaces.len() != NUM_SPACES_PER_VIAL as usize {
            return Err(format!(
                "Wrong number of spaces in vial: expected {}, got {}",
                NUM_SPACES_PER_VIAL,
                spaces.len()
            )
            .into());
        }
        let vial: Vial = spaces
            .into_iter()
            .map(|s| Color::unknown(&s))
            .collect::<Vec<_>>()
            .try_into()
            .map_err(|_| "Wrong number of spaces")?;
        vials.push(vial);
    }

    let game = Game::create(vials);

    let mut settings = game.settings.borrow_mut();
    settings.level = level.to_string();
    settings.had_mystery_spaces = special_modes.contains(&MYSTERY_MODE_FLAG);
    settings.drain_mode =
        special_modes.contains(&DRAIN_MODE_FLAG) || special_modes.contains(&DRAIN_MODE_FLAG_2);
    settings.blind_mode = special_modes.contains(&BLIND_MODE_FLAG);
    drop(settings);

    Ok(game)
}
