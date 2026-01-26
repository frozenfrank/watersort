/// Main entry point for the Water Sort Puzzle CLI

// use watersort::Game;
// use watersort::types::Vial;

use watersort::core::{Color, ColorCodeAllocator, color::{EMPTY_SPACE, UNKNOWN_VALUE}};

fn main() {
    println!("Water Sort Puzzle Solver - Rust Edition");
    create_color_allocator();
    create_game();
}

fn create_color_allocator() {
    let mut allocator = ColorCodeAllocator::new();

    // Unknown Values
    print_color_with_code_stats(&mut allocator, UNKNOWN_VALUE);
    print_color_with_code_stats(&mut allocator, "?");
    print_color_with_code_stats(&mut allocator, UNKNOWN_VALUE);

    // Empty values
    print_color_with_code_stats(&mut allocator, EMPTY_SPACE);
    print_color_with_code_stats(&mut allocator, "-");
    print_color_with_code_stats(&mut allocator, EMPTY_SPACE);

    // Short color values
    print_color_with_code_stats(&mut allocator, "b");
    print_color_with_code_stats(&mut allocator, "lb");
    print_color_with_code_stats(&mut allocator, "gn");
    print_color_with_code_stats(&mut allocator, "m");
    print_color_with_code_stats(&mut allocator, "y");
    print_color_with_code_stats(&mut allocator, "b");

    // Long color values
    print_color_with_code_stats(&mut allocator, "blue");
    print_color_with_code_stats(&mut allocator, "lightblue");
    print_color_with_code_stats(&mut allocator, "green");
    print_color_with_code_stats(&mut allocator, "mint");
    print_color_with_code_stats(&mut allocator, "yellow");
    print_color_with_code_stats(&mut allocator, "blue");

    // Review standard colors
    print_color_with_code_stats(&mut allocator, UNKNOWN_VALUE);
    print_color_with_code_stats(&mut allocator, EMPTY_SPACE);
}

fn print_color_with_code_stats(allocator: &mut ColorCodeAllocator<'_>, color_name: &str) {
    let code = &Color(color_name);
    let color_code = allocator.assign_code(code);
    println!("Color Code [{} = {}, code = {:p}, str = {:p}]", color_name, color_code, code, code.0);
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
