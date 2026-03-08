use rand::{rngs::ThreadRng, seq::SliceRandom};
use std::fmt::Display;
use std::{
    cmp::max,
    collections::{HashSet, VecDeque},
    fmt::Debug,
    sync::Arc,
    time::Instant,
};

use crate::display::debug::debug_games;
use crate::{
    Game, INITIAL_SOLVER_QUEUE_CAP,
    display::print_vials,
    solver::{SolveMethod, strategy::SolverStrategy},
};

// ### Structs ###

pub struct BaseSolver<'a, S: SolverStrategy> {
    pub seed_game: Arc<Game<'a>>,
    q: VecDeque<Arc<Game<'a>>>,
    pub state: SolverState,
    pub strategy: S,

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

#[derive(Default, Debug)]
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

#[derive(Default, Debug)]
pub struct SolutionStats {
    pub num_iterations: usize,
    pub num_dead_ends: usize,
    pub num_partial_solutions_generated: usize,
    pub num_swallowed_games_found: usize,
    pub num_unique_states_computed: usize,
    pub num_duplicate_games: usize,
    pub max_queue_length: usize,
}

#[derive(Debug)]
pub struct SolverState {
    pub reset: bool,
    pub quit: bool,
    pub solve_method: SolveMethod,
    pub search_bfs: bool,
    pub shuffle_next_moves: bool,

    pub rng: ThreadRng,

    pub find_solutions_count: usize,
    pub find_solutions_remaining: usize,
}

#[derive(Debug)]
pub struct QueueCheckData<'a> {
    pub state: &'a SolverState,
    pub stats: &'a SolutionStats,
    pub solution: &'a BestSolution<'a>,
    pub timing: &'a SolutionTiming,

    pub current_game: &'a Game<'a>,
    pub q_len: usize,
}

// ### Implementations ###

impl<'a, S: SolverStrategy> BaseSolver<'a, S> {
    pub fn new(
        strategy: S,
        seed_game: Arc<Game<'a>>,
        solve_method: SolveMethod,
        num_solutions: usize,
    ) -> Self {
        BaseSolver {
            seed_game,
            strategy,
            q: VecDeque::with_capacity(INITIAL_SOLVER_QUEUE_CAP),
            state: SolverState::new(solve_method, num_solutions),
            solution_timing: Default::default(),
            solution_min: Default::default(),
            recent_solution_stats: Default::default(),
        }
    }

    /// Intelligent search through all the possible game states until we find a solution.
    /// This rust implementation does not support discovering new values.
    pub fn find_solutions(&mut self) {
        println!("============== Debugging find_solutions ==============");
        println!("{:#?}", self.seed_game.settings.borrow());
        println!("{:#?}", self.state);

        self.solution_timing.solution_set_start = Some(Instant::now());

        while self.state.reset
            || self.solution_min.result.is_none()
            || self.state.find_solutions_remaining > 0
        {
            self.state.reset = false;
            if !self.strategy.on_init_solution_attempt(false) {
                break;
            }

            let _ = self.next_solution();

            self.solution_timing.solution_start = Some(Instant::now());
            self.solution_timing.solution_end = None;

            // Setup our search
            let mut expect_solution = true;
            let mut computed = HashSet::<Arc<Game>>::with_capacity(1000);

            self.q.push_back(self.seed_game.clone());
            self.state.search_bfs = self.state.solve_method.searches_bfs();

            self.recent_solution_stats = Default::default();
            self.recent_solution_stats.max_queue_length = 1;

            // Perform the search
            loop {
                if self.solution_min.result.is_some() {
                    break;
                }
                if self.state.reset || self.state.quit {
                    expect_solution = false;
                    break;
                }

                debug_games("\nQueue State", &self.q);
                let current = match self.next_game_state() {
                    Some(game) => game,
                    None => break,
                };

                // println!("Selected game: \n{:?}", current);
                // print_vials(&current);

                // Launch on_iteration_report hook
                self.recent_solution_stats.num_iterations += 1;
                if self.recent_solution_stats.num_iterations % 100000 == 0 {
                    let queue_check = self.produce_queue_check_data(current.as_ref());
                    let continue_searching = self.strategy.on_iteration_report(&queue_check);
                    if !continue_searching {
                        expect_solution = false;
                        self.state.quit = true;
                    }
                }

                // Prune if we've found a cheaper solution
                if !self.state.search_bfs
                    && let Some(min) = self.solution_min.result.as_ref()
                    && min.num_moves() <= current.num_moves()
                {
                    self.solution_min.num_abandoned += 1;
                    break;
                }

                // Check all next moves
                let mut has_net_new_next_game = false;
                let mut next_games = current.generate_next_games();
                let has_no_next_games = next_games.is_empty();
                if self.state.reset || self.state.quit {
                    // Break out after user input
                    expect_solution = false;
                    break;
                }

                // debug_games(&format!("Next games ({})", next_games.len()), &next_games);

                if self.state.shuffle_next_moves {
                    next_games.shuffle(&mut self.state.rng);
                    debug_games(&format!("Shuffled games ({})", next_games.len()), &next_games);
                }
                for next_game in next_games {
                    self.recent_solution_stats.num_partial_solutions_generated += 1;

                    let newly_inserted = computed.insert(next_game.clone());
                    if !newly_inserted {
                        self.recent_solution_stats.num_duplicate_games += 1;
                        continue;
                    }

                    has_net_new_next_game = true;
                    if next_game.is_finished() {
                        self.solution_timing.solution_end = Some(Instant::now());
                        if self
                            .strategy
                            .on_solution_found(&next_game, &mut self.solution_min)
                        {
                            break; // Finish searching
                        }
                    } else {
                        self.q.push_back(next_game);
                    }
                }

                // Maintain stats
                self.recent_solution_stats.max_queue_length =
                    max(self.recent_solution_stats.max_queue_length, self.q.len());
                if has_no_next_games {
                    self.recent_solution_stats.num_dead_ends += 1;
                    self.strategy.on_dead_end_found(current.as_ref());
                } else if !has_net_new_next_game {
                    self.recent_solution_stats.num_swallowed_games_found += 1;
                }
            }

            if self.solution_timing.solution_end.is_none() {
                self.solution_timing.solution_end = Some(Instant::now());
            }
            self.recent_solution_stats.num_unique_states_computed = computed.len();
            if expect_solution && self.solution_min.result.is_none() {
                let try_again = self.strategy.on_impossible_game();
                if !try_again {
                    break; // There are no solutions
                }
            }
        }

        self.solution_timing.solution_set_end = Some(Instant::now());
    }

    fn add_game_states<C>(&mut self, mut games: Vec<Arc<Game<'a>>>) {
        if self.state.shuffle_next_moves {
            games.shuffle(&mut self.state.rng);
        }
        self.q.extend(games);
    }

    fn next_solution(&mut self) -> bool {
        if self.state.find_solutions_remaining > 0 {
            self.q.clear();
            self.solution_min.num_attempted += 1;
            self.state.find_solutions_remaining -= 1;
            return true;
        } else {
            return false;
        }
    }

    fn next_game_state(&mut self) -> Option<Arc<Game<'a>>> {
        if self.state.search_bfs {
            self.q.pop_front()
        } else {
            self.q.pop_back()
        }
    }

    fn produce_queue_check_data(&'a self, current_game: &'a Game<'a>) -> QueueCheckData<'a> {
        QueueCheckData {
            state: &self.state,
            stats: &self.recent_solution_stats,
            solution: &self.solution_min,
            timing: &self.solution_timing,

            q_len: self.q.len(),
            current_game,
        }
    }
}

impl SolverState {
    pub fn new(solve_method: SolveMethod, mut num_solutions: usize) -> Self {
        if num_solutions < 1 || !solve_method.accepts_multiple_attempts() {
            num_solutions = 1;
        }

        Self {
            reset: false,
            quit: false,

            solve_method,
            search_bfs: solve_method.searches_bfs(),
            shuffle_next_moves: solve_method.shuffles_moves(),
            rng: Default::default(),

            find_solutions_count: num_solutions,
            find_solutions_remaining: num_solutions,
        }
    }
}

fn format_duration<'a>(start: &Option<Instant>, end: &Option<Instant>) -> String {
    if let Some(start) = start
        && let Some(end) = end
    {
        format!("{:?}", &end.duration_since(*start))
    } else {
        format!(
            "Incomplete information. Has start: {}, Has end: {}",
            start.is_some(),
            end.is_some()
        )
    }
}

impl Debug for SolutionTiming {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SolutionTiming")
            .field(
                "solution",
                &format_duration(&self.solution_start, &self.solution_end),
            )
            .field(
                "solution_set",
                &format_duration(&self.solution_set_start, &self.solution_set_end),
            )
            .finish()
    }
}

impl<'a> Display for QueueCheckData<'a> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let now = Instant::now();

        // Standard stats (all usize)
        let stats = [
            ("resets", self.solution.num_attempted),
            ("itrs", self.stats.num_iterations),
            ("mvs", self.current_game.num_moves()),
            ("q len", self.q_len),
            ("ends", self.stats.num_dead_ends),
            ("dups", self.stats.num_duplicate_games),
            ("mins", 0), // Placeholder for minutes
        ];
        write!(f, "QUEUE CHECK: ")?;
        for (key, value) in stats {
            write!(f, "\t{}: {}", key, value)?;
        }

        // Special stats
        if let Some(start) = self.timing.solution_start {
            write!(f, "\tsol: {:.1?}", now.duration_since(start));
        }
        if self.solution.num_attempted > 0 && let Some(set_start) = self.timing.solution_set_start {
            write!(f, "\tset: {:.1?}", now.duration_since(set_start));
        }

        Ok(())
    }
}
