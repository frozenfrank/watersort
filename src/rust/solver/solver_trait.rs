use std::sync::Arc;

use crate::{
    Game,
    solver::{
        SolveMethod,
        base_solver::{BestSolution, SolutionStats, SolutionTiming},
    },
};

pub trait Solver<'a> {
    fn new(game: Arc<Game<'a>>, solve_method: SolveMethod) -> Self;
    fn solve_game(&mut self);
    fn get_results(&self) -> &'_ BestSolution<'a>;
    fn get_stats(&self) -> &SolutionStats;
    fn get_timing(&self) -> &SolutionTiming;
    fn set_debug(&mut self, debug: crate::solver::SolverDebugLevel);
}
