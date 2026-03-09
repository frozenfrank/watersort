use std::sync::Arc;

use crate::{
    DEFAULT_SOLVE_METHOD, Game, SOLVER_DEBUG_LEVEL, display::{print_moves, print_vials}, solver::{SolveMethod, Solver, solution::solution_solver::SolutionSolver, solve_method}
};

pub fn solve_game(game: Arc<Game<'_>>, solve_method: SolveMethod) {
    println!("{:?}", game.settings.borrow().allocator);

    let mut solver = SolutionSolver::new(game, solve_method);
    solver.set_debug(SOLVER_DEBUG_LEVEL);

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
