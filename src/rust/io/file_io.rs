use std::fs::File;
use std::io::{BufWriter, Write};
use crate::core::Game;
use crate::core::game_settings::GameSettings;

pub fn save_game(game: &std::sync::Arc<Game>, path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let file = File::create(path)?;
    let mut writer = BufWriter::new(file);

    writeln!(&mut writer, "i")?;
    let settings = *game.settings.borrow();

    let special_modes = get_special_modes(&settings);
    let level_line = format!("{} {}", settings.level, special_modes.join(" "));
    writeln!(file, "{}", level_line.trim())?;
    writeln!(file, "{}", game.num_vials())?;
    for vial in &settings.original_vials {
        let line = vial.join("\t");
        writeln!(file, "{}", line)?;
    }
    Ok(())
}

fn get_special_modes(settings: &GameSettings) -> Vec<&str> {
    let mut modes = Vec::<&str>::new();

    if settings.drain_mode {
        modes.push(&"drain");
    }
    if settings.blind_mode {
        modes.push(&"blind");
    }
    if settings.had_mystery_spaces {
        modes.push(&"mystery");
    }

    modes
}
