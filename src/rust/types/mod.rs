/// Type definitions and aliases for the Water Sort Puzzle engine
pub mod constants;

use crate::core::{Color, ColorCode};

use self::constants::NUM_SPACES_PER_VIAL;

/// Represents a 0-based index retrieving a vial from all vials
pub type VialIndex = u8;
/// Represents a 0-based index into a single vial
pub type SpaceIndex = u8;

/// The size to use when storing game and other numbers of comparable size
pub type DepthSize = u8;

/// A vial is a column containing colored liquids, represented as characters
/// Each vial has exactly NUM_SPACES_PER_VIAL spaces
pub type Vial = [Color; NUM_SPACES_PER_VIAL];

/// A move is represented as (source_vial_index, destination_vial_index)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Move {
    pub from: VialIndex,
    pub to: VialIndex,
}

impl Move {
    pub fn new(from: VialIndex, to: VialIndex) -> Self {
        Move { from, to }
    }
}

/// Information about a move that has been executed
/// (color_moved, num_moved, is_complete, vacated_vial, started_vial)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MoveInfo<'a> {
    pub color_moved: &'a Color,
    pub num_moved: DepthSize,
    pub is_complete: bool,
    pub vacated_vial: bool,
    pub started_vial: bool,
}

/// Represents a single completion in the game
/// (color, depth_when_completed)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Completion {
    pub color: ColorCode,
    pub depth: DepthSize,
}
