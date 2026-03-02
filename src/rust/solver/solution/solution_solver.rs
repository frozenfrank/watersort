// SolutionSolver struct: wraps BaseSolver, implements Solver trait

use std::sync::Arc;

use crate::solver::solution::solution_strategy::SolutionStrategy;
use crate::solver::{SolveMethod, Solver};
use crate::solver::base_solver::{BaseSolver, BestSolution, SolutionStats, SolutionTiming};
use crate::{DEFAULT_DFR_SEARCH_ATTEMPTS, Game};


pub struct SolutionSolver<'a> {
    base: BaseSolver<'a, SolutionStrategy>,
}

impl<'a> Solver<'a> for SolutionSolver<'a> {
    fn new(game: Arc<Game<'a>>, solve_method: SolveMethod) -> Self {
        let num_solutions = DEFAULT_DFR_SEARCH_ATTEMPTS;
        todo!()
    }

    fn solve_game(&mut self) {
        // To be implemented
    }

    fn get_results(&self) -> &BestSolution {
        &self.base.solution_min
    }

    fn get_stats(&self) -> &SolutionStats {
        &self.base.recent_solution_stats
    }

    fn get_timing(&self) -> &SolutionTiming {
        &self.base.solution_timing
    }
}
