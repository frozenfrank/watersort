use std::sync::Arc;

use crate::{Game, Move, MoveInfo};

pub struct SolutionStep<'a> {
    pub game: Arc<Game<'a>>,
    pub move_: Option<Move>,
    pub move_info: MoveInfo<'a>,
    pub is_same_as_previous: Option<bool>,
}

impl<'a> SolutionStep<'a> {
    pub fn new(game: &Arc<Game<'a>>) -> Self {
        Self {
            game: game.clone(),
            move_: game.last_move(),
            move_info: game.get_move_info(),
            is_same_as_previous: None,
        }
    }
}
