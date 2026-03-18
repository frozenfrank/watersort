use std::rc::Rc;

use crate::{Game, Move, MoveInfo};

pub struct SolutionStep<'a> {
    pub game: Rc<Game<'a>>,
    pub data: Option<SolutionStepMove>,
    pub is_same_as_previous: Option<bool>,
}

pub struct SolutionStepMove {
    pub move_: Move,
    pub move_info: MoveInfo,
}

impl<'a> SolutionStep<'a> {
    pub fn new(game: &Rc<Game<'a>>) -> Self {
        let mut out = Self {
            game: game.clone(),
            data: None,
            is_same_as_previous: None,
        };

        if let Some(move_) = game.last_move() {
            out.data = Some(SolutionStepMove {
                move_,
                move_info: game.get_move_info().unwrap(),
            });
        }

        out
    }
}
