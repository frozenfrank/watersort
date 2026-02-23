// SafeGameSolver struct: wraps BaseSolver, implements Solver trait

use super::base_solver::BaseSolver;
use super::solver_trait::Solver;

pub struct SafeGameSolver<'a> {
    pub base: BaseSolver<'a>,
}

impl<'a> Solver for SafeGameSolver<'a> {
    fn solve_game(&mut self) {
        // To be implemented
    }
}
