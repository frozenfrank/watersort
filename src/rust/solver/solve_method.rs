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
