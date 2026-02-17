use std::fmt::Write;
use std::{
    ops::{Deref, DerefMut},
    sync::{LazyLock, Mutex},
};

use crate::display::util::write_vial_color_text;
use crate::types::solution_step::SolutionStep;
use crate::{
    Game,
    display::solution_step_preparer::{GameInputType, SolutionStepPreparer},
    types::StdResult,
};

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

    let chars_per_line = 100; // Estimates with the python version show 80-90 per line. A little extra won't hurt.
    let mut output = String::with_capacity(chars_per_line * steps.len());

    writeln!(&mut output, "Moves ({steps}){mode}:", steps = steps.len(), mode = (if settings.drain_mode {" [Drain Gameplay]"} else {""}))?;
    if steps.len() == 0 {
        writeln!(&mut output, "{INDENT}None")?;
    } else {
        for step in steps {
            write!(&mut output, "{INDENT}")?;
            write_move_str(&mut output, step);
            writeln!(&mut output)?;
        }
    }

    print!("{}", output);
    Ok(())
}

/// Writes a string with a fixed justification, including escape character for formatting, that describes the move.
fn write_move_str(s: &mut String, step: SolutionStep) {
    if step.move_.is_none() {
        return;
    }
    let move_text = format!("{}", step.move_.unwrap());
    write_vial_color_text(s, &step.move_info.color_moved, &move_text, 8, false);
}
