use std::{fmt::Write, sync::Arc};

use arrayvec::ArrayVec;

use crate::{Game, display::print_moves::{CHARS_PER_LINE, PrintMovesCache, write_move_str}, types::{StdResult, solution_step::SolutionStep}};

const MAX_GAME_OUTPUT: usize = 20;
const WRITE_EXPECTATION: &str = "String buffer accepts debug data";

pub fn debug_games<'a, T>(description: &str, games: T)
where
    T: IntoIterator<Item = &'a Arc<Game<'a>>>,
    T::IntoIter: ExactSizeIterator + DoubleEndedIterator,
{
    let games = games.into_iter();
    let num_games = games.len();
    let mut output = String::with_capacity(CHARS_PER_LINE * (num_games + 1));
    do_debug_games(&mut output, description, games, num_games).expect(WRITE_EXPECTATION);
    println!("{}", output);
}

fn do_debug_games<'a>(output: &mut String, description: &str, games: impl DoubleEndedIterator<Item = &'a Arc<Game<'a>>>, num_games: usize) -> StdResult {
    let mut games = games.peekable();

    writeln!(output, "{}:", description)?;
    let first_game = match games.peek().cloned() {
        Some(game) => game,
        None => {
            writeln!(output, "  None")?;
            return Ok(());
        }
    };

    let settings = first_game.settings.borrow();
    let print_moves_cache = PrintMovesCache::new(&settings.allocator);

    writeln!(output, "  Idx:\t Depth\t Last Move")?;
    let max_output_games = first_game.num_vials().clamp(7, MAX_GAME_OUTPUT);
    if num_games < max_output_games {
        debug_game_range(output, &print_moves_cache, games.enumerate())?;
    } else {
        let half_output_games = max_output_games >> 2;
        let mut begin_buffer = ArrayVec::<GameIndexed<'a>, MAX_GAME_OUTPUT>::new();
        let mut end_buffer = ArrayVec::<GameIndexed<'a>, MAX_GAME_OUTPUT>::new();

        // Take first N/2 games
        for i in 0..half_output_games {
            match games.next() {
                Some(game) => begin_buffer.push((i, game)),
                None => break,
            }
        }

        // Take last N/2 games, in reverse
        for i in 0..half_output_games {
            match games.next_back() {
                Some(game) => end_buffer.push((num_games-1-i, game)),
                None => break,
            }
        }

        debug_game_range(output, &print_moves_cache, begin_buffer.into_iter())?;
        writeln!(output, "  ...")?;
        debug_game_range(output, &print_moves_cache, end_buffer.into_iter().rev())?;
    }

    Ok(())
}

type GameIndexed<'a> = (usize, &'a Arc<Game<'a>>);

fn debug_game_range<'a>(output: &mut impl Write, print_moves_cache: &PrintMovesCache, games: impl Iterator<Item = GameIndexed<'a>>) -> StdResult {
    for (idx, game) in games {
        write!(output, "  {}:\t {}\t", idx, game.num_moves())?;

        let step = &SolutionStep::new(&game);
        write_move_str(output, step, print_moves_cache)?;
        writeln!(output, "")?;
    }
    Ok(())
}
