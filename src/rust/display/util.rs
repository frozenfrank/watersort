use std::fmt::Write;

use crate::{core::Color, display::colorama_ansi::STYLE, types::StdResult};

pub fn print_lines(lines: Vec<String>) {
    // Write the results to stdout using different traits than the rest of this file.
    use std::io::{Write, stdout};

    let mut lock = stdout().lock();
    lines
        .iter()
        .for_each(|line| writeln!(lock, "{}", line).unwrap());
}

pub fn write_vial_color(s: &mut impl Write, color: &Color, foreground_only: bool) -> StdResult {
    if let Some(style) = if foreground_only {
        &color.style_secondary
    } else {
        &color.style_primary
    } {
        s.write_str(&style)?;
    }

    Ok(())
}

pub fn write_vial_color_text(
    s: &mut impl Write,
    color: &Color,
    text: &str,
    ljust: usize,
    foreground_only: bool,
) -> StdResult {
    write_vial_color(s, color, foreground_only)?;

    s.write_str(text)?;
    s.write_str(&STYLE["RESET_ALL"])?;

    if ljust <= text.len() {
        return Ok(());
    }

    for _ in 0..(ljust - text.len()) {
        s.write_char(' ')?;
    }
    Ok(())
}
