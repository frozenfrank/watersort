// Defines the Solver trait: shared interface for all solvers

pub trait Solver {
    fn solve_game(&mut self);
    // Add more methods as needed for interchangeability
}
