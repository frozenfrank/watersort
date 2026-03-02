use crate::solver::{generic_solver::GenericSolver, safe_game::safe_game_strategy::SafeGameStrategy};

pub type SafeGameSolver<'a> = GenericSolver<'a, SafeGameStrategy>;
