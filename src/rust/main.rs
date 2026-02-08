/// Main entry point for the Water Sort Puzzle CLI
use watersort::{
    Game,
    io::{parser, save_game_to_file},
};

// Use Display impl on `Game` for printing

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <level> <output_file>", args[0]);
        std::process::exit(1);
    }

    let level = &args[1];

    let mut game: Game = parser::read_game_level(level)?;
    println!("{}", game);

    game.apply_move(0, game.num_vials()-1);
    println!("{}", game);

    game.apply_move(0, game.num_vials()-2);
    println!("{}", game);

    if args.len() >= 3 {
        let output_path = &args[2];
        save_game_to_file(&game, output_path)?;
    }

    Ok(())
}
