/// Water Sort Puzzle Solver - Rust implementation
///
/// A high-performance Rust port of the Water Sort Puzzle solver,
/// maintaining feature parity with the original Python implementation
/// while achieving better memory efficiency and performance.
pub mod core;
pub mod display;
pub mod io;
pub mod play;
pub mod types;
pub mod utils;

// Re-export commonly used types
pub use core::Game;
pub use types::{Completion, Move, MoveInfo};
pub use utils::constants::*;
