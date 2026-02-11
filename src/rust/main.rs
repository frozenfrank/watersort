use std::sync::Arc;

/// Main entry point for the Water Sort Puzzle CLI
use watersort::{
    Game, Move,
    io::{parser, save_game_to_file},
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args: Vec<String> = std::env::args().collect();
    if cfg!(debug_assertions) && args.len() < 2 {
        args.push(String::from("1")); // Debugging - fix the level input
    }
    if args.len() < 2 {
        eprintln!("Usage: {} <level> <output_file>", args[0]);
        std::process::exit(1);
    }

    let level = &args[1];

    let mut game: Game = parser::read_game_level(level)?;
    println!("{}", game);

    {
        let settings = game.settings.borrow();
        println!("{:?}\n", settings);
        println!("{:?}\n", settings.allocator);
        println!("{:?}\n", game);
    }

    let mut move_valid: bool;
    move_valid = game.apply_move(0, game.num_vials() - 1);
    println!("Move Valid: {}\n{}", move_valid, game);

    move_valid = game.apply_move(0, game.num_vials() - 2);
    println!("Move Valid: {}\n{}", move_valid, game);

    move_valid = game.apply_move(1, 0);
    println!("Move Valid: {}\n{}", move_valid, game);

    {
        let game = Arc::new(game.clone());
        let game2 = game.spawn(Move { from: 0, to: 1 });
        println!("Spawned game:\n{}\n{:?}", game2, game2);

        let move_ = Move { from: 1, to: 2 };
        let game3 = game2.spawn(move_);
        println!("Applied move: {:?}\n{}\n{:#?}", move_, game3, game3);
    }

    println!("Root game: {}\n{:#?}", game.is_root(), game);

    if args.len() >= 3 {
        let output_path = &args[2];
        save_game_to_file(&game, output_path)?;
    }

    Ok(())
}
