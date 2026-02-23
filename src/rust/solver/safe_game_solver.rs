// SafeGameSolver struct: wraps BaseSolver, implements Solver trait

use super::base_solver::BaseSolver;
use super::solver_trait::Solver;

pub struct SafeGameSolver<'a> {
    pub base: BaseSolver<'a>,
}

impl<'a> Solver<'a> for SafeGameSolver<'a> {
    fn new(game: std::sync::Arc<crate::Game<'a>>, solve_method: super::SolveMethod) -> Self {
        todo!()
    }

    fn solve_game(&mut self) {
        todo!()
    }

    fn get_results(&self) -> &super::base_solver::BestSolution {
        todo!()
    }

    fn get_stats(&self) -> &super::base_solver::SolutionStats {
        todo!()
    }

    fn get_timing(&self) -> &super::base_solver::SolutionTiming {
        todo!()
    }
}
