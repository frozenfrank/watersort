// SafeGameSolver struct: wraps BaseSolver, implements Solver trait

use super::base_solver::BaseSolver;
use super::solver_trait::Solver;

pub struct SafeGameSolver {
    pub base: BaseSolver,
}

impl Solver for SafeGameSolver {
    fn solve_game(&mut self) {
        // To be implemented
    }
}
