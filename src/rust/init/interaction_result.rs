use crate::init::Mode;

/// Represents the User's choice of intended utility behavior
#[derive(Default)]
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
    pub solve_method: Option<String>,
}
