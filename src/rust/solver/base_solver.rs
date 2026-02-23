use std::{collections::VecDeque, sync::Arc, time::Instant};

use crate::Game;

pub struct BaseSolver<'a> {
    pub seed_game: Arc<Game<'a>>,
    pub state: SolverState<'a>,

    pub solution_timing: SolutionTiming,
    pub solution_min: BestSolution<'a>,

    pub recent_solution_stats: SolutionStats,
}

pub struct SolutionTiming {
    pub solution_set_start: Option<Instant>,
    pub solution_set_end: Option<Instant>,
    pub solution_start: Option<Instant>,
    pub solution_end: Option<Instant>,
}

pub struct BestSolution<'a> {
    /// The best solution found so far
    pub result: Option<Arc<Game<'a>>>,
    /// Number of times a new solution was attempted from scratch
    pub num_attempted: usize,
    /// Number of times we located an improved `min` solution
    pub num_updates: usize,
    /// Number of times we abandoned a solution because it was not as good as the `min` solution
    pub num_abandoned: usize,
}

pub struct SolutionStats {
    pub num_iterations: usize,
    pub num_dead_ends: usize,
    pub num_partial_solutions_generated: usize,
    pub num_swallowed_games_found: usize,
    pub num_unique_states_computed: usize,
    pub num_duplicate_games: usize,
    pub max_queue_length: usize,
}

pub struct SolverState<'a> {
    pub search_bfs: bool,
    pub q: VecDeque<Arc<Game<'a>>>,
    pub find_solutions_count: usize,
    pub find_solutions_remaining: usize,
}
