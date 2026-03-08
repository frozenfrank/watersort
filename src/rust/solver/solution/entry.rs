use std::sync::Arc;

use crate::{
    DEFAULT_SOLVE_METHOD, Game, display::{print_moves, print_vials}, solver::{Solver, solution::solution_solver::SolutionSolver}
};

pub fn solve_game(game: Arc<Game<'_>>) {
    println!("{:?}", game.settings.borrow().allocator);

    let mut solver = SolutionSolver::new(game, DEFAULT_SOLVE_METHOD);

    solver.solve_game();

    println!("Timing: {:#?}", solver.get_timing());
    println!("Stats: {:#?}", solver.get_stats());
    // println!("Results: {:#?}", solver.get_results());

    if let Some(min_solution) = &solver.get_results().result {
        print_vials(min_solution);
        print_moves(min_solution);
    } else {
        println!("No solution.");
    }
}
