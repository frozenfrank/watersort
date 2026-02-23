// AnalysisSolver struct: wraps BaseSolver, implements Solver trait

use crate::solver::{Solver, analysis::MoveDepthCounter, base_solver::BaseSolver};

pub struct AnalysisSolver<'a> {
    pub base: BaseSolver<'a>,
}

pub struct AnalysisSummaryData {
    pub partial_depth: MoveDepthCounter,
    pub dup_game_depth: MoveDepthCounter,
    pub swallowed_depth: MoveDepthCounter,
    pub dead_end_depth: MoveDepthCounter,
    pub solution_depth: MoveDepthCounter,
    pub unique_sols_depth: MoveDepthCounter,
    // Not yet represented
    // pub sol_find_seconds: bool,
    // pub unique_solutions: bool,
    // pub is_unique_list: bool,
}

impl<'a> Solver for AnalysisSolver<'a> {
    fn solve_game(&mut self) {
        unimplemented!("AnalysisSolver: solve_game");
    }
}
