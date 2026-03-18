use std::rc::Rc;

use crate::{core::Color, types::DepthSize};

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct MoveInfo {
    pub color_moved: Rc<Color>,
    pub num_moved: DepthSize,
    pub is_complete: bool,
    pub vacated_vial: bool,
    pub started_vial: bool,
}
