// SafeGameSolver struct: wraps BaseSolver, implements Solver trait

use crate::solver::{SolveMethod, Solver, base_solver::{BaseSolver, BestSolution, SolutionStats, SolutionTiming}, safe_game::safe_game_strategy::SafeGameStrategy, strategy::SolverStrategy};

pub struct SafeGameSolver<'a> {
    pub base: BaseSolver<'a, SafeGameStrategy>,
}

impl<'a> Solver<'a> for SafeGameSolver<'a> {
    fn new(_game: std::sync::Arc<crate::Game<'a>>, _solve_method: SolveMethod) -> Self {
        todo!()
    }

    fn solve_game(&mut self) {
        todo!()
    }

    fn get_results(&self) -> &BestSolution<'a> {
        todo!()
    }

    fn get_stats(&self) -> &SolutionStats {
        todo!()
    }

    fn get_timing(&self) -> &SolutionTiming {
        todo!()
    }
}
