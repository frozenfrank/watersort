use std::{collections::VecDeque, sync::Arc};

use crate::{Game, Move, types::solution_step::SolutionStep};

#[derive(Default)]
pub struct SolutionStepPreparer {
    /// The presence of this field indicates that the value should be updated.
    last_printed_moves: Option<VecDeque<Move>>,
}

pub type SolutionStepsResult<'a> = VecDeque<SolutionStep<'a>>;


impl<'a> SolutionStepPreparer {
    pub fn prepare_solution_steps(&mut self, game: &'a Arc<Game<'a>>) -> SolutionStepsResult<'a> {
        self.do_prepare_solution_steps(game, None)
    }

    pub fn prepare_solution_steps_from(&mut self, game: &'a Arc<Game<'a>>, from_game: &Game) -> SolutionStepsResult<'a> {
        self.do_prepare_solution_steps(game, Some(from_game))
    }

    fn do_prepare_solution_steps(
        &mut self,
        game: &'a Arc<Game<'a>>,
        from_game: Option<&Game>,
    ) -> SolutionStepsResult<'a> {
        let mut steps = VecDeque::with_capacity(game.num_moves());
        if game.last_move().is_none() {
            self.last_printed_moves = None;
            return steps;
        }

        // Collect moves
        let mut curr_game = Some(game);
        let mut moves = VecDeque::with_capacity(game.num_moves());
        loop {
            let game = match curr_game {
                Some(game) => game,
                None => break,
            };

            if Some(game.as_ref()) == from_game {
                return steps; // Skip comparison against previous prints
            }

            // Do something fancy for many lines
            let move_ = match game.last_move() {
                Some(move_) => move_,
                None => break,
            };

            moves.push_front(move_);
            steps.push_front(SolutionStep {
                game: curr_game.unwrap().clone(),
                move_: Some(move_),
                move_info: game.get_move_info().unwrap(),
                is_same_as_previous: None,
            });

            curr_game = game.prev();
        }

        // Compare to previous printed moves
        if let Some(prev_moves) = &self.last_printed_moves {
            let mut i = 0;
            while i < prev_moves.len() && i < moves.len() {
                if prev_moves[i] == moves[i] {
                    steps[i].is_same_as_previous = Some(true);
                } else {
                    steps[i].is_same_as_previous = Some(false);
                    break; // All subsequent moves are different
                }
                i += 1;
            }
        }

        self.last_printed_moves = Some(moves);
        return steps;
    }
}
