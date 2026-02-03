use std::fs::File;
use std::io::{BufRead, BufReader};
use crate::core::{ColorCodeAllocator, Game};
use crate::core::Color;
use crate::types::Vial;
use crate::types::constants::NUM_SPACES_PER_VIAL;

pub fn read_game_file(path: &str) -> Result<(ColorCodeAllocator, std::sync::Arc<Game>), Box<dyn std::error::Error>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut lines = reader.lines();

    let mode = lines.next().ok_or("No mode line")??;
    if mode != "i" {
        return Err("Unsupported mode".into());
    }

    let level_line: String = lines.next().ok_or("No level line")??;
    let level_parts: Vec<String> = level_line.split_whitespace().map(|s| s.to_string()).collect();
    let level = level_parts.get(0).cloned().unwrap_or_default();
    let special_modes: Vec<String> = level_parts[1..].to_vec();

    let num_vials_str = lines.next().ok_or("No num vials line")??;
    let num_vials: usize = num_vials_str.trim().parse()?;

    let mut vials: Vec<Vial> = Vec::new();
    for _ in 0..num_vials {
        let line = lines.next().ok_or("Not enough vial lines")??;
        let spaces: Vec<String> = line.split_whitespace().map(|s| s.to_string()).collect();
        if spaces.len() != NUM_SPACES_PER_VIAL as usize {
            return Err(format!("Wrong number of spaces in vial: expected {}, got {}", NUM_SPACES_PER_VIAL, spaces.len()).into());
        }
        let vial: Vial = spaces.into_iter().map(|s| Color(s)).collect::<Vec<_>>().try_into().map_err(|_| "Wrong number of spaces")?;
        vials.push(vial);
    }

    let had_mystery_spaces = special_modes.contains(&"mystery".to_string());
    let mut allocator = ColorCodeAllocator::new();
    let game = Game::create(&mut allocator, vials, level, special_modes, had_mystery_spaces);
    Ok((allocator, game))
}
