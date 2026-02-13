use std::io::{self, Write};

use crate::core::Game;

/// Interactive play loop ported from the Python `playGame` helper.
pub fn play_game(game: &Game) {
    let root_game = game;
    let mut game = game.clone();

    println!("Play the game:");
    println!("  r         reset");
    println!("  q         quit");
    println!("  NUM NUM   move from vial to vial");

    loop {
        // Print minimal state for the user
        println!("Moves: {}", game.num_moves());
        println!("{}", game);

        print!("Enter command: ");
        // ensure prompt is visible
        io::stdout().flush().ok();

        let mut input = String::new();
        if io::stdin().read_line(&mut input).is_err() {
            println!("Failed to read input. Try again.");
            continue;
        }

        let input = input.trim();
        if input.is_empty() {
            continue;
        }
        if input == "q" {
            break;
        }
        if input == "r" {
            game = root_game.clone();
            continue;
        }

        let parts: Vec<&str> = input.split_whitespace().collect();
        if parts.len() != 2 {
            println!("Invalid command. Enter two vial numbers, e.g. '1 3'");
            continue;
        }

        let start: usize = match parts[0].parse::<usize>() {
            Ok(n) if n >= 1 => n - 1,
            _ => {
                println!("Invalid start vial number");
                continue;
            }
        };
        let end: usize = match parts[1].parse::<usize>() {
            Ok(n) if n >= 1 => n - 1,
            _ => {
                println!("Invalid end vial number");
                continue;
            }
        };

        if start >= game.num_vials() || end >= game.num_vials() {
            println!("Vial index out of range (1..={})", game.num_vials());
            continue;
        }

        if !game.can_move(start, end) {
            println!("That move is invalid");
            continue;
        }

        // Perform the move mutably
        let applied = game.apply_move(start, end);
        if !applied {
            println!("Move failed (internal)");
            continue;
        }

        if game.is_finished() {
            println!("Final state:\n{}", game);
            println!("Congratulations, you solved it!\n");
            break;
        }
    }

    println!("Goodbye.");
}
