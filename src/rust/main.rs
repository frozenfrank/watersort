/// Main entry point for the Water Sort Puzzle CLI

use std::env;
use watersort::io::{parser, file_io};

fn display_game(game: &std::sync::Arc<watersort::core::Game>) {
    println!("Level: {}", game.settings.level);
    println!("Special modes: {:?}", game.settings.special_modes);
    for i in 0..game.num_vials() as usize {
        print!("Vial {}: ", i + 1);
        for j in 0..4 as usize {
            let color_str = &game.settings.original_vials[i][j];
            print!("{} ", color_str);
        }
        println!();
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <input_file> <output_file>", args[0]);
        std::process::exit(1);
    }

    let input_path = &args[1];
    let output_path = &args[2];

    let (_allocator, game) = parser::read_game_file(input_path)?;

    display_game(&game);

    file_io::save_game(&game, output_path)?;

    println!("Saved to {}", output_path);

    Ok(())
}
