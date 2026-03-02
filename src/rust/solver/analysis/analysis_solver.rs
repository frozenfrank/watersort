// AnalysisSolver struct: wraps BaseSolver, implements Solver trait

use crate::solver::analysis::analysis_strategy::AnalysisStrategy;
use crate::solver::{Solver, analysis::MoveDepthCounter, base_solver::BaseSolver};

pub struct AnalysisSolver<'a> {
    pub base: BaseSolver<'a, AnalysisStrategy>,
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

impl<'a> Solver<'a> for AnalysisSolver<'a> {
    fn new(
        game: std::sync::Arc<crate::Game<'a>>,
        solve_method: crate::solver::SolveMethod,
    ) -> Self {
        todo!()
    }

    fn solve_game(&mut self) {
        todo!()
    }

    fn get_results(&self) -> &crate::solver::base_solver::BestSolution<'a> {
        todo!()
    }

    fn get_stats(&self) -> &crate::solver::base_solver::SolutionStats {
        todo!()
    }

    fn get_timing(&self) -> &crate::solver::base_solver::SolutionTiming {
        todo!()
    }
}
