use crate::solver::{analysis::analysis_strategy::AnalysisStrategy, generic_solver::GenericSolver};

pub type AnalysisSolver<'a> = GenericSolver<'a, AnalysisStrategy>;
