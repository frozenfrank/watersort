use crate::{init::Mode, solver::SolveMethod};

/// Represents the User's choice of intended utility behavior
#[derive(Debug)]
pub struct InteractionResult {
    pub mode: Mode,
    /// A non-empty Level identifier
    pub level: Option<String>,
    /// None means ask the user; otherwise, True/False
    pub known_drain_mode: Option<bool>,
    /// None means ask the user; otherwise, True/False
    pub known_blind_mode: Option<bool>,
    /// If the mode supports repeating actions, this is the number of times to repeat the action.
    pub num_iterations: usize,
    /// Only required for some Modes
    pub solve_method: Option<SolveMethod>,
    /// Indicates if the user is entering Game information, compared to reading input from a file
    pub user_interacting: bool,
}

impl Default for InteractionResult {
    fn default() -> Self {
        Self {
            mode: Default::default(),
            level: Default::default(),
            known_drain_mode: Default::default(),
            known_blind_mode: Default::default(),
            num_iterations: Default::default(),
            solve_method: Default::default(),
            user_interacting: true,
        }
    }
}
