/// Internal debugging module for ColorCodeAllocator
/// Tests color code allocation, deallocation, and memory management
use crate::core::{
    Color, ColorCodeAllocator,
    color::{EMPTY_SPACE, UNKNOWN_VALUE},
};

pub fn run_color_allocator_debug() {
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

fn print_color_with_code_stats(allocator: &mut ColorCodeAllocator, color_name: &str) {
    let color = Color::new(color_name);
    let color_code = allocator.assign_code(&color);
    let managed_color = allocator.interpret_code(color_code);
    println!(
        "Color Code [{} = {}, color ~ {:p}, str ~ {:p}, managed_color ~ {:p}, managed_string ~ {:p}]",
        color_name, color_code, &color, &color.0, managed_color, &managed_color.0
    );
}
