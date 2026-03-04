use std::fmt::Write;
use std::{
    ops::{Deref, DerefMut},
    sync::{LazyLock, Mutex},
};

use crate::MoveInfo;
use crate::core::ColorCodeAllocator;
use crate::display::colorama_ansi::STYLE;
use crate::display::print_moves_consts::*;
use crate::display::text_formatted::TextFormatted;
use crate::display::util::write_vial_color_text;
use crate::types::solution_step::SolutionStep;
use crate::{
    Game,
    display::solution_step_preparer::{GameInputType, SolutionStepPreparer},
    types::StdResult,
};

pub const CHARS_PER_LINE: usize = 100; // Estimates with the python version show 80-90 per line. A little extra won't hurt.


const INDENT: &str = "  ";
const SEPARATOR: &str = "\t ";
const WRITE_EXPECTATION: &str = "Moves print to std";

static PREPARER: LazyLock<Mutex<SolutionStepPreparer>> =
    LazyLock::new(|| Mutex::new(SolutionStepPreparer::default()));

/// Prints out the moves taken to reach this game state.
pub fn print_moves(game: GameInputType) {
    do_print_moves(game, None).expect(WRITE_EXPECTATION);
}

/// Prints out the moves taken to reach this game state, showing only the steps to reach it from from_game.
pub fn print_moves_from(game: GameInputType, from_game: &Game) {
    do_print_moves(game, Some(from_game)).expect(WRITE_EXPECTATION);
}

fn do_print_moves(game: GameInputType, from_game: Option<&Game>) -> StdResult {
    let mut mutex_guard = PREPARER.deref().lock()?;
    let preparer = mutex_guard.deref_mut();
    let settings = game.settings.borrow();

    let steps = preparer.do_prepare_solution_steps(game, from_game);

    let mut output = String::with_capacity(CHARS_PER_LINE * steps.len());

    writeln!(
        &mut output,
        "Moves ({steps}){mode}:",
        steps = steps.len(),
        mode = if settings.drain_mode {
            " [Drain Gameplay]"
        } else {
            ""
        }
    )?;
    if steps.len() == 0 {
        writeln!(&mut output, "{INDENT}None")?;
    } else {
        let cache = PrintMovesCache::new(&settings.allocator);
        for step in steps {
            write!(&mut output, "{INDENT}")?;
            write_move_str(&mut output, &step, &cache);
            if let Some(is_same_as_prev) = step.is_same_as_previous {
                let word = if is_same_as_prev {
                    &"(same)"
                } else {
                    &"(different)"
                };
                write!(&mut output, "{}{}", SEPARATOR, word)?;
            }
            writeln!(&mut output)?;
        }
    }

    print!("{}", output);
    Ok(())
}

/// Writes a string with a fixed justification, including escape character for formatting, that describes the move.
pub fn write_move_str(s: &mut String, step: &SolutionStep, cache: &PrintMovesCache) {
    let move_data = match &step.data {
        Some(data) => data,
        None => return,
    };

    let move_text = format!("{}", move_data.move_);
    write_vial_color_text(s, &move_data.move_info.color_moved, &move_text, 8, false);
    write_move_info_str(s, &move_data.move_info, cache);
}

/// Writes a string with fixed justification, including escape sequences for formatting, that describes MoveInfo.
fn write_move_info_str(s: &mut String, info: &MoveInfo, cache: &PrintMovesCache) {
    // "({num_moved} {color}{extra_str})      " Justified to a standard width
    let mut output = TextFormatted::default();
    let const_width: usize = 5;
    let color_width: usize;
    let extra_width: usize;

    output.push_text(&"("); // 1 char

    let num_moved = info.num_moved.to_string(); // Assume 1 char
    let num_moved_fmt = if info.num_moved > 1 {
        &STYLE["BRIGHT"]
    } else {
        &""
    };
    output.concat(&TextFormatted::normal(num_moved_fmt, &num_moved));

    output.push_text(&" "); // 1 char
    if cache.print_full_color_name {
        output.push_text(info.color_moved.name.unwrap_or(&info.color_moved.key));
        color_width = cache.max_color_name_len;
    } else {
        output.push_text(&info.color_moved.key);
        color_width = 2;
    }

    #[rustfmt::skip]
    let extra_str = match &info {
        MoveInfo {  is_complete: true, ..} => &cache.consts.complete,
        MoveInfo { vacated_vial: true, .. } => &cache.consts.vacated,
        MoveInfo { started_vial: true, ..} => &cache.consts.started,
        _ => &TextFormatted::default(),
    };
    if extra_str.len_text() > 0 {
        output.push_text(&" "); // 1 char
        output.concat(extra_str); // cache.consts.max_width chars
    }
    extra_width = cache.consts.max_width;

    output.push_text(&")"); // 1 char

    output.left_justify(const_width + color_width + extra_width);
    s.write_str(output.as_str())
        .expect("Output is able to write into the String buffer");
}

pub struct PrintMovesCache<'a> {
    max_color_name_len: usize,
    print_full_color_name: bool,
    consts: &'a PrintMovesConsts,
}

impl<'a> PrintMovesCache<'a> {
    pub fn new(allocator: &ColorCodeAllocator) -> Self {
        Self {
            max_color_name_len: allocator.max_color_name_len(),
            consts: PRINT_MOVES_CONSTS.deref(),
            print_full_color_name: true,
        }
    }
}
