/// Type definitions and aliases for the Water Sort Puzzle engine

pub mod constants;

use self::constants::NUM_SPACES_PER_VIAL;

/// A vial is a column containing colored liquids, represented as characters
/// Each vial has exactly NUM_SPACES_PER_VIAL spaces
pub type Vial = [char; NUM_SPACES_PER_VIAL];

/// A move is represented as (source_vial_index, destination_vial_index)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Move {
    pub from: usize,
    pub to: usize,
}

impl Move {
    pub fn new(from: usize, to: usize) -> Self {
        Move { from, to }
    }
}

/// Information about a move that has been executed
/// (color_moved, num_moved, is_complete, vacated_vial, started_vial)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MoveInfo {
    pub color_moved: char,
    pub num_moved: usize,
    pub is_complete: bool,
    pub vacated_vial: bool,
    pub started_vial: bool,
}

/// Represents a single completion in the game
/// (color, depth_when_completed)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Completion {
    pub color: char,
    pub depth: usize,
}
