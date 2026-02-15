use crate::{core::Color, display::colorama_ansi::STYLE};

pub fn print_lines(lines: Vec<String>) {
    // Write the results to stdout using different traits than the rest of this file.
    use std::io::{Write, stdout};

    let mut lock = stdout().lock();
    lines
        .iter()
        .for_each(|line| writeln!(lock, "{}", line).unwrap());
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
