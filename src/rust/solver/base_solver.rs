use std::{collections::VecDeque, sync::Arc, time::Instant};

use crate::{Game, INITIAL_SOLVER_QUEUE_CAP};

pub struct BaseSolver<'a> {
    pub seed_game: Arc<Game<'a>>,
    pub state: SolverState<'a>,

    pub solution_timing: SolutionTiming,
    pub solution_min: BestSolution<'a>,

    pub recent_solution_stats: SolutionStats,
}

#[derive(Default)]
pub struct SolutionTiming {
    pub solution_set_start: Option<Instant>,
    pub solution_set_end: Option<Instant>,
    pub solution_start: Option<Instant>,
    pub solution_end: Option<Instant>,
}

#[derive(Default)]
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

#[derive(Default)]
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

impl<'a> BaseSolver<'a> {
    pub fn new(seed_game: Arc<Game<'a>>, num_solutions: usize, search_bfs: bool) -> Self {
        BaseSolver {
            seed_game,
            state: SolverState::new(num_solutions, search_bfs),
            solution_timing: Default::default(),
            solution_min: Default::default(),
            recent_solution_stats: Default::default(),
        }
    }
}

impl<'a> SolverState<'a> {
    pub fn new(num_solutions: usize, search_bfs: bool) -> Self {
        Self {
            search_bfs,
            q: VecDeque::with_capacity(INITIAL_SOLVER_QUEUE_CAP),
            find_solutions_count: num_solutions,
            find_solutions_remaining: num_solutions,
        }
    }

    pub fn next_solution(&mut self) -> bool {
        self.q.clear();
        if self.find_solutions_remaining > 0 {
            self.find_solutions_remaining -= 1;
            return true;
        } else {
            return false;
        }
    }

    pub fn next_state(&mut self) -> Option<Arc<Game<'a>>> {
        if self.search_bfs {
            self.q.pop_front()
        } else {
            self.q.pop_back()
        }
    }
}
