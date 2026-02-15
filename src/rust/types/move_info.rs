use crate::{core::Color, types::DepthSize};

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
