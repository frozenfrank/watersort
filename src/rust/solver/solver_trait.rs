use std::sync::Arc;

use crate::{
    Game,
    solver::{
        SolveMethod,
        base_solver::{BestSolution, SolutionStats, SolutionTiming},
        solve_method,
    },
};

pub trait Solver<'a> {
    fn new(game: Arc<Game<'a>>, solve_method: SolveMethod) -> Self;
    fn solve_game(&mut self);
    fn get_results(&self) -> &BestSolution;
    fn get_stats(&self) -> &SolutionStats;
    fn get_timing(&self) -> &SolutionTiming;
}
