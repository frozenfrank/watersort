/// Main entry point for the Water Sort Puzzle CLI
use std::env;
use watersort::{
    Game,
    io::{parser, save_game_to_file},
};

// Use Display impl on `Game` for printing

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <level> <output_file>", args[0]);
        std::process::exit(1);
    }

    let level = &args[1];
    let output_path = &args[2];

    let mut game: Arc<Game> = parser::read_game_level(level)?;

    println!("{}", game);

    save_game_to_file(&game, output_path)?;

    Ok(())
}
