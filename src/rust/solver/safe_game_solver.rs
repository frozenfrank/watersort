// SafeGameSolver struct: wraps BaseSolver, implements Solver trait

use super::base_solver::BaseSolver;
use super::solver_trait::Solver;

use super::strategy::SolverStrategy;

pub struct SafeGameSolver<'a, S: SolverStrategy> {
    pub base: BaseSolver<'a, S>,
}

impl<'a, S: SolverStrategy> Solver<'a> for SafeGameSolver<'a, S> {
    fn new(_strategy: S, _game: std::sync::Arc<crate::Game<'a>>, _solve_method: super::SolveMethod) -> Self {
        todo!()
    }

    fn solve_game(&mut self) {
        todo!()
    }

    fn get_results(&self) -> &super::base_solver::BestSolution<'a> {
        todo!()
    }

    fn get_stats(&self) -> &super::base_solver::SolutionStats {
        todo!()
    }

    fn get_timing(&self) -> &super::base_solver::SolutionTiming {
        todo!()
    }
}
