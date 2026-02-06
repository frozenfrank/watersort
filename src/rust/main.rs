/// Main entry point for the Water Sort Puzzle CLI
use std::env;
use watersort::{
    io::{file_io, parser},
    types::constants::NUM_SPACES_PER_VIAL,
};

fn display_game(game: &std::sync::Arc<watersort::core::Game>) {
    let settings = game.settings.borrow();

    println!("Level: {}", settings.level);
    println!("Mystery: {}", settings.had_mystery_spaces);
    println!("Had Unknowns: {}", settings.has_unknowns);
    println!("Drain mode: {}", settings.drain_mode);

    for vial_idx in 0..game.num_vials() {
        print!("Vial {}: ", vial_idx + 1);
        for space_idx in 0..NUM_SPACES_PER_VIAL {
            let color_str = game.get_vial_space(vial_idx, space_idx);
            print!("{} ", color_str);
        }
        println!();
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

    let (_allocator, game) = parser::read_game_level(level)?;

    display_game(&game);

    file_io::save_game_to_file(&game, output_path)?;

    Ok(())
}
