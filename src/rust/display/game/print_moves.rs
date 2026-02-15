use std::collections::VecDeque;

use crate::{Game, Move};

/// Represents the moves printed most recently
type Moves = VecDeque<Move>;

static PREV_PRINTED_MOVES: Option<Moves> = None;

pub fn print_moves(game: &Game) {
    do_print_moves(game, None);
}

pub fn print_moves_from(game: &Game, from_game: &Game) {
    do_print_moves(game, Some(from_game));
}

fn do_print_moves(game: &Game, from_game: Option<&Game>) {
    unimplemented!()
}
