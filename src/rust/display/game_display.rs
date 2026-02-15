// Game display module for watersort (Rust)
// Ported and adapted from the Python implementation

use crate::core::game::Game;
use crate::core::color::Color;
use crate::types::constants::NUM_SPACES_PER_VIAL;

pub fn print_vials(game: &Game, number_spaces: bool) {
    let num_spaces = NUM_SPACES_PER_VIAL;
    let num_vials = game.num_vials();
    let mut lines: Vec<Vec<String>> = vec![vec![]; num_spaces + 1];

    if number_spaces {
        for line_index in 0..=num_spaces {
            lines[line_index].push(if line_index == 0 { " ".to_string() } else { (line_index).to_string() });
        }
    }
    for i in 0..num_vials {
        lines[0].push(format!("\t{}", i + 1));
    }
    for space_index in 0..num_spaces {
        for vial_index in 0..num_vials {
            let color = &game.get_vial_color(vial_index)[space_index];
            lines[space_index + 1].push(format!("\t{}", format_vial_color(color, color, 0, false)));
        }
    }
    for line in lines {
        println!("{}", line.join(""));
    }
}

pub fn print_vials_dense(game: &Game) {
    let num_spaces = NUM_SPACES_PER_VIAL;
    let num_vials = game.num_vials();
    let mut out = String::new();
    for vial in 0..num_vials {
        for space in 0..num_spaces {
            let color = &game.get_vial_color(vial)[space];
            let s = format_space_ref(color);
            out.push_str(&s);
            if s.len() < 2 {
                out.push(' ');
            }
        }
    }
    println!("{}", out);
}

/// Formats a color for display in a vial (with ANSI if available)
pub fn format_vial_color(color: &Color, _ref_color: &Color, _width: usize, _dense: bool) -> String {
    if let Some(style) = &color.style_primary {
        format!("{}{}\x1b[0m", style, color.key)
    } else {
        color.key.clone()
    }
}

/// Formats a color for dense display (single char, no ANSI)
pub fn format_space_ref(color: &Color) -> String {
    color.key.clone()
}
