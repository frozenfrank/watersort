use std::fmt::Display;

use crate::types::VialIndex;

/// A move is represented as (source_vial_index, destination_vial_index)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Move {
    pub from: VialIndex,
    pub to: VialIndex,
}

impl Move {
    /// Creates a Move given 0-indexed vial numbers
    pub fn new(from: VialIndex, to: VialIndex) -> Self {
        Move { from, to }
    }

    /// Creates a Move provided human-friendly vial numbers
    pub fn vials(from: VialIndex, to: VialIndex) -> Self {
        Move {
            from: from - 1,
            to: to - 1,
        }
    }
}

impl Display for Move {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_fmt(format_args!("{}->{}", self.from + 1, self.to + 1))
    }
}
