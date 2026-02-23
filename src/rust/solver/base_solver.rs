use std::{collections::VecDeque, sync::Arc, time::Instant};

use crate::{Game, INITIAL_SOLVER_QUEUE_CAP, solver::SolveMethod};

// ### Structs ###

pub struct BaseSolver<'a> {
    pub seed_game: Arc<Game<'a>>,
    q: VecDeque<Arc<Game<'a>>>,
    pub state: SolverState,

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

pub struct SolverState {
    pub solve_method: SolveMethod,
    pub search_bfs: bool,
    pub shuffle_next_moves: bool,

    pub find_solutions_count: usize,
    pub find_solutions_remaining: usize,
}

// ### Implementations ###

impl<'a> BaseSolver<'a> {
    pub fn new(seed_game: Arc<Game<'a>>, solve_method: SolveMethod, num_solutions: usize) -> Self {
        BaseSolver {
            seed_game,
            q: VecDeque::with_capacity(INITIAL_SOLVER_QUEUE_CAP),
            state: SolverState::new(solve_method, num_solutions),
            solution_timing: Default::default(),
            solution_min: Default::default(),
            recent_solution_stats: Default::default(),
        }
    }

    pub fn add_game_states<C>(&mut self, games: C)
    where
        C: IntoIterator<Item = Arc<Game<'a>>>,
    {
        if self.state.shuffle_next_moves {
            unimplemented!("Add game states shuffled");
        } else {
            self.q.extend(games);
        }
    }

    pub fn next_solution(&mut self) -> bool {
        self.q.clear();

        if self.state.find_solutions_remaining > 0 {
            self.state.find_solutions_remaining -= 1;
            return true;
        } else {
            return false;
        }
    }

    pub fn next_game_state(&mut self) -> Option<Arc<Game<'a>>> {
        if self.state.search_bfs {
            self.q.pop_front()
        } else {
            self.q.pop_back()
        }
    }
}

impl SolverState {
    pub fn new(solve_method: SolveMethod, mut num_solutions: usize) -> Self {
        if !solve_method.accepts_multiple_attempts() {
            num_solutions = 1;
        }

        Self {
            solve_method,
            search_bfs: solve_method.searches_bfs(),
            shuffle_next_moves: solve_method.shuffles_moves(),

            find_solutions_count: num_solutions,
            find_solutions_remaining: num_solutions,
        }
    }
}
