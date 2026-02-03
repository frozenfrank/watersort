use std::fs::File;
use std::io::Write;
use crate::core::Game;

pub fn save_game(game: &std::sync::Arc<Game>, path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let mut file = File::create(path)?;
    writeln!(file, "i")?;
    let settings = *game.settings.borrow();
    let level_line = format!("{} {}", settings.level, settings.special_modes.join(" "));
    writeln!(file, "{}", level_line.trim())?;
    writeln!(file, "{}", game.num_vials())?;
    for vial in &settings.original_vials {
        let line = vial.join("\t");
        writeln!(file, "{}", line)?;
    }
    Ok(())
}
