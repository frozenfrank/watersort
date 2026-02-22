// SolutionSolver struct: wraps BaseSolver, implements Solver trait

use super::base_solver::BaseSolver;
use super::solver_trait::Solver;

pub struct SolutionSolver {
    pub base: BaseSolver,
}

impl Solver for SolutionSolver {
    fn solve_game(&mut self) {
        // To be implemented
    }
}
