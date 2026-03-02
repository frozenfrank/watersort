// SolutionSolver struct: wraps BaseSolver, implements Solver trait

use std::sync::Arc;

use crate::solver::SolveMethod;
use crate::{DEFAULT_DFR_SEARCH_ATTEMPTS, Game};

use super::base_solver::BaseSolver;
use super::solver_trait::Solver;
use super::strategy::SolverStrategy;

pub struct SolutionSolver<'a, S: SolverStrategy> {
    base: BaseSolver<'a, S>,
}

impl<'a, S: SolverStrategy> Solver<'a> for SolutionSolver<'a, S> {
    fn new(strategy: S, game: Arc<Game<'a>>, solve_method: SolveMethod) -> Self {
        let num_solutions = DEFAULT_DFR_SEARCH_ATTEMPTS;
        Self {
            base: BaseSolver::new(strategy, game, solve_method, num_solutions),
        }
    }

    fn solve_game(&mut self) {
        // To be implemented
    }

    fn get_results(&self) -> &super::base_solver::BestSolution {
        &self.base.solution_min
    }

    fn get_stats(&self) -> &super::base_solver::SolutionStats {
        &self.base.recent_solution_stats
    }

    fn get_timing(&self) -> &super::base_solver::SolutionTiming {
        &self.base.solution_timing
    }
}
