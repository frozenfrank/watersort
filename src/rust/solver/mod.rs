#![allow(unused)]

mod analysis;
mod base_solver;
mod generic_solver;
mod safe_game;
mod solution;
mod solve_method;
mod solver_trait;
mod strategy;

pub use solution::entry::solve_game;
pub use solve_method::SolveMethod;
pub use solver_trait::Solver;
