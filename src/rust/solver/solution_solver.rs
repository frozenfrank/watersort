// SolutionSolver struct: wraps BaseSolver, implements Solver trait

use super::base_solver::BaseSolver;
use super::solver_trait::Solver;

pub struct SolutionSolver<'a> {
    pub base: BaseSolver<'a>,
}

impl<'a> Solver for SolutionSolver<'a> {
    fn solve_game(&mut self) {
        // To be implemented
    }
}
