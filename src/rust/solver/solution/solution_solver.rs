use crate::solver::generic_solver::GenericSolver;
use crate::solver::solution::solution_strategy::SolutionStrategy;

pub type SolutionSolver<'a> = GenericSolver<'a, SolutionStrategy>;
