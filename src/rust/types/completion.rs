use crate::{core::ColorCode, types::DepthSize};

/// Represents a single completion in the game
/// (color, depth_when_completed)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Completion {
    pub color: ColorCode,
    pub depth: DepthSize,
}
