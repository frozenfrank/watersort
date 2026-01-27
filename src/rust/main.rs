/// Main entry point for the Water Sort Puzzle CLI

// use watersort::Game;
// use watersort::types::Vial;

use watersort::core::{run_color_allocator_debug};

fn main() {
    println!("Water Sort Puzzle Solver - Rust Edition");
    run_color_allocator_debug();
    create_game();
}


fn create_game() {
    // Example: Create a simple game
    // let vial1: Vial = ['r', 'r', 'b', 'b'];
    // let vial2: Vial = ['g', 'g', 'y', 'y'];
    // let vial3: Vial = ['-', '-', '-', '-'];

    // let game = Game::new_root(vec![vial1, vial2, vial3]);

    // println!("Game created with {} vials", game.num_vials());
    // println!("Game is finished: {}", game.is_finished());
}
