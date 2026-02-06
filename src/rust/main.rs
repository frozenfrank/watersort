/// Main entry point for the Water Sort Puzzle CLI
use std::env;
use watersort::core::{Game};
use watersort::io::{parser, save_game_to_file};

fn display_game(game: &Game) {
    let settings = game.settings.borrow();

    println!("Level: {}", settings.level);
    println!("Mystery: {}", settings.had_mystery_spaces);
    println!("Had Unknowns: {}", settings.has_unknowns);
    println!("Drain mode: {}", settings.drain_mode);

    for vial_idx in 0..game.num_vials() {
        let colors = game.get_vial_color(vial_idx).map(|color| color.0.clone());
        println!("Vial {}: {}", vial_idx + 1, colors.join(" "));
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <level> <output_file>", args[0]);
        std::process::exit(1);
    }

    let level = &args[1];
    let output_path = &args[2];

    let game = parser::read_game_level(level)?;

    display_game(&game);

    save_game_to_file(&game, output_path)?;

    Ok(())
}
