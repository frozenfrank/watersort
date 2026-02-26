pub trait SolverStrategy {

    /// Called before attempting a new solution. Return True to proceed with the solution.
    fn on_init_solution_attempt(&mut self, bypass_error_correction: bool) -> bool {
        // First correct any errors in the game
        // If not bypass_error_correction and self.seedGame.attemptCorrectErrors() { return false; }
        // NOTE: This is a stub. Implement error correction logic in concrete types.
        true
    }

    /// Called when the iteration search count exceeds REPORT_ITERATION_FREQ. Return True to continue searching.
    fn on_iteration_report(&mut self, current: &Game) -> bool {
        // If not self._searchBFS { println!("Checked {} iterations.", self.numIterations); }
        // NOTE: This is a stub. Implement reporting logic in concrete types.
        true
    }

    /// Called when a new solution is found. Return True to stop this attempt with the discovered solution
    fn on_solution_found(&mut self, solution: &Game) -> bool {
        // if not self.minSolution or solution._numMoves < self.minSolution._numMoves:
        //     self.minSolution = solution
        //     self.minSolutionUpdates += 1
        // self.solutionDepth[solution._numMoves] += 1
        // self.solFindSeconds[int((self.solutionEnd - self.solutionStart + 0.9) // 1)] += 1
        // ... hash and uniqueness logic ...
        // NOTE: This is a stub. Implement solution tracking logic in concrete types.
        true
    }

    /// Called when a dead end is found.
    fn on_dead_end_found(&mut self, dead_end: &Game) {
        // pass
        // NOTE: This is a stub. Implement dead end handling in concrete types.
    }

    /// Print queue check stats.
    fn print_queue_check(&self, current: &Game) {
        // Print stats about the queue and search progress.
        // NOTE: This is a stub. Implement stats printing in concrete types.
    }

    /// Called when it is detected that no solutions exist. Return true to reset and try again.
    fn on_impossible_game(&mut self) -> bool {
        // message = formatVialColor("er", "This game has no solution.");
        // message += " Type YES if you have corrected the game state and want to try searching again."
        // retryRsp = self.seedGame.requestVal(message, printOptions=True, printState=False)
        // return retryRsp == "YES"
        // NOTE: This is a stub. Implement retry logic in concrete types.
        false
    }

    /// Called after _findSolutions() completes. Use this to report on the discovered solution.
    fn on_after_find_solutions(&mut self) {
        // self.print_queue_check();
        // println!("Found solution requiring {{}} moves.", self.minSolution.getDepth());
        // NOTE: This is a stub. Implement reporting logic in concrete types.
    }
}
