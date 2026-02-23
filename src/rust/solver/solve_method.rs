#[derive(Clone, Copy)]
pub enum SolveMethod {
    /// Depth-First Search
    DFS,
    /// Depth-First Search (Randomized)
    DFR,
    /// Breath-First Search -- Very slow
    BFS,
    /// BFS until an inflection point, then DFR
    MIX,
}

impl SolveMethod {
    pub fn shuffles_moves(self) -> bool {
        match self {
            SolveMethod::DFR => true,
            SolveMethod::MIX => false, // This is a special case, but in general, the answer is no.
            _ => false,
        }
    }

    pub fn accepts_multiple_attempts(self) -> bool {
        match self {
            SolveMethod::DFR => true,
            _ => false,
        }
    }

    /// Whether this method *initially* begins by searching in BFS mode.
    pub fn searches_bfs(self) -> bool {
        match self {
            SolveMethod::BFS | SolveMethod::MIX => true,
            _ => false,
        }
    }
}
