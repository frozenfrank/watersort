/// Water Sort Puzzle Solver - Rust implementation
///
/// A high-performance Rust port of the Water Sort Puzzle solver,
/// maintaining feature parity with the original Python implementation
/// while achieving better memory efficiency and performance.

pub mod core;
pub mod types;
pub mod utils;

// Re-export commonly used types
pub use types::{Move, MoveInfo, Completion};
pub use core::Game;
