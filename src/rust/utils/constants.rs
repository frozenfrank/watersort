use crate::{init::Mode, solver::SolveMethod};

/// Game constants that define the structure of Water Sort Puzzle games

/// Number of spaces per vial/glass in the game
pub const NUM_SPACES_PER_VIAL: usize = 4;

/// Threshold for determining when we have "few" vials
pub const FEW_VIALS_THRESHOLD: usize = 5;

/// Solver and analyzer version numbers
pub const SOLVER_VERSION: u32 = 4;
pub const ANALYZER_VERSION: u32 = 6;

// ### Choose interaction defaults ###

pub const DEFAULT_ANALYZE_ATTEMPTS: usize = 100;
pub const DEFAULT_DFR_SEARCH_ATTEMPTS: usize = 100;
pub const FORCE_SOLVE_LEVEL: Option<&str> = Some(&"2");
pub const FORCE_INTERACTION_MODE: Option<Mode> = None;
pub const DEFAULT_SOLVE_METHOD: SolveMethod = SolveMethod::DFS;
pub const INITIAL_SOLVER_QUEUE_CAP: usize = 200;
