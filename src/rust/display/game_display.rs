// Game display module for watersort (Rust)
// Ported and adapted from the Python implementation

use crate::NUM_SPACES_PER_VIAL;
use crate::core::color::Color;
use crate::core::game::Game;
use crate::display::colorama_ansi::STYLE;
use crate::types::StdResult;
use std::fmt::Write;

pub fn print_vials(game: &Game) -> StdResult {
    print_vials_numbered(game, false)
}

/// Prints the vials of a game, optionally numbering each output line for uniques in debuggers
pub fn print_vials_numbered(game: &Game, number_spaces: bool) -> StdResult {
    let num_vials = game.num_vials();
    let reserve_chars_per_vial = 60; // Formatting can be 40 chars (fore + back styles)
    let mut lines: Vec<String> =
        vec![String::with_capacity(num_vials * reserve_chars_per_vial); NUM_SPACES_PER_VIAL + 1];

    if number_spaces {
        write!(&mut lines[0], " ")?;
        for line in 1..=NUM_SPACES_PER_VIAL {
            write!(&mut lines[line], "{}", line)?;
        }
    }

    for i in 0..num_vials {
        write!(&mut lines[0], "\t{}", i + 1)?;
    }

    let allocator = &game.settings.borrow().allocator;
    let all_spaces = game.get_spaces_code();
    let mut cur_idx = 0;
    for _vial_index in 0..num_vials {
        for space_index in 0..NUM_SPACES_PER_VIAL {
            let color = allocator.interpret_code_as_ref(all_spaces[cur_idx]);
            let s = &mut lines[space_index + 1];
            s.push('\t');
            write_vial_color_text(s, color, &color.key, 0, false);
            cur_idx += 1;
        }
    }

    print_lines(lines);
    Ok(())
}

pub fn write_vial_color(s: &mut String, color: &Color, foreground_only: bool) {
    if let Some(style) = if foreground_only {
        &color.style_secondary
    } else {
        &color.style_primary
    } {
        s.push_str(&style);
    }
}

pub fn write_vial_color_text(
    s: &mut String,
    color: &Color,
    text: &str,
    ljust: usize,
    foreground_only: bool,
) {
    write_vial_color(s, color, foreground_only);

    s.push_str(text);
    s.push_str(&STYLE["RESET_ALL"]);

    if ljust <= text.len() {
        return;
    }
    for _ in 0..(ljust - text.len()) {
        s.push(' ');
    }
}

pub fn write_space_ref(s: &mut String, vial_idx: usize, space_idx: usize) -> StdResult {
    write!(s, "{}:{}", vial_idx + 1, space_idx + 1)?;
    Ok(())
}

fn print_lines(lines: Vec<String>) {
    // Write the results to stdout using different traits than the rest of this file.
    use std::io::{Write, stdout};

    let mut lock = stdout().lock();
    lines
        .iter()
        .for_each(|line| writeln!(lock, "{}", line).unwrap());
}
