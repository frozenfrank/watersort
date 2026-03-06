use std::{fmt::Write, sync::Arc};

use crate::{Game, display::print_moves::{CHARS_PER_LINE, PrintMovesCache, write_move_str}, types::{StdResult, solution_step::SolutionStep}};


pub fn debug_games_ary<'a>(description: &str, games: &[Arc<Game<'a>>]) {
    let mut output = String::with_capacity(CHARS_PER_LINE * (games.len() + 1));
    do_debug_games_ary(&mut output, description, games).expect("String buffer accepts debug data");
    println!("{}", output);
}

fn do_debug_games_ary<'a>(output: &mut String, description: &str, games: &[Arc<Game<'a>>]) -> StdResult {
    writeln!(output, "{}:", description)?;
    if games.is_empty() {
        writeln!(output, "  None")?;
        return Ok(());
    }

    let first_game = &games[0];
    let settings = first_game.settings.borrow();
    let print_moves_cache = PrintMovesCache::new(&settings.allocator);

    writeln!(output, "  Idx:\t Depth\t Last Move")?;
    let max_output_games = first_game.num_vials().clamp(5, 20);
    if games.len() < max_output_games {
        debug_game_range(output, &print_moves_cache, games.iter().enumerate())?;
    } else {
        let half_output_games = max_output_games >> 2;
        let iter_first_n = games.iter().enumerate().take(half_output_games);
        let end_iter_idx = games.len() - half_output_games;
        let iter_last_n = games[end_iter_idx..].iter().enumerate().map(|(i, game)| (i + end_iter_idx, game));

        debug_game_range(output, &print_moves_cache, iter_first_n)?;
        writeln!(output, "  ...")?;
        debug_game_range(output, &print_moves_cache, iter_last_n)?;
    }

    Ok(())
}

fn debug_game_range<'a>(output: &mut impl Write, print_moves_cache: &PrintMovesCache, games: impl Iterator<Item = (usize, &'a Arc<Game<'a>>)>) -> StdResult {
    for (idx, game) in games {
        write!(output, "  {}\t {}\t", idx, game.num_moves())?;

        let step = &SolutionStep::new(game);
        write_move_str(output, step, print_moves_cache)?;
        writeln!(output, "")?;
    }
    Ok(())
}
