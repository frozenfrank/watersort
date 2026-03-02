// GenericSolver struct: wraps BaseSolver with a custom Strategy

use std::sync::Arc;

use crate::Game;
use crate::solver::base_solver::{BaseSolver, BestSolution, SolutionStats, SolutionTiming};
use crate::solver::strategy::SolverStrategy;
use crate::solver::{SolveMethod, Solver};

pub struct GenericSolver<'a, S: SolverStrategy + Default> {
    base: BaseSolver<'a, S>,
}

impl<'a, S: SolverStrategy + Default> Solver<'a> for GenericSolver<'a, S> {
    fn new(game: Arc<Game<'a>>, solve_method: SolveMethod) -> Self {
        let strategy = S::default();
        let num_solutions = strategy.default_num_solutions();
        Self {
            base: BaseSolver::new(strategy, game, solve_method, num_solutions),
        }
    }

    fn solve_game(&mut self) {
        self.base.find_solutions()
    }

    fn get_results(&self) -> &'_ BestSolution<'a> {
        &self.base.solution_min
    }

    fn get_stats(&self) -> &SolutionStats {
        &self.base.recent_solution_stats
    }

    fn get_timing(&self) -> &SolutionTiming {
        &self.base.solution_timing
    }
}
