use crate::types::VialIndex;


/// Shared global settings for a game tree
/// Stored once on the root game to avoid duplication
#[derive(Debug, Clone)]
pub struct GameSettings {
    /// The level identifier (e.g., "263")
    pub level: String,
    /// The number of vials represented by this game
    pub num_vials: VialIndex,
    /// Whether this game has been modified from disk
    pub modified: bool,
    /// Whether there are color errors in the vials
    pub color_error: bool,
    /// Whether there are unknown values
    pub has_unknowns: bool,
    /// Drain mode: colors drain from the bottom instead of pouring from top
    pub drain_mode: bool,
    /// Blind mode: spaces re-hide after moving
    pub blind_mode: bool,
    /// Whether mystery spaces have been discovered
    pub had_mystery_spaces: bool,
    /// Special modes as strings for file compatibility
    pub special_modes: Vec<String>,
    /// Original vial strings for saving
    pub original_vials: Vec<Vec<String>>,
}

impl Default for GameSettings {
    fn default() -> Self {
        GameSettings {
            level: String::new(),
            num_vials: 0,
            modified: false,
            color_error: false,
            has_unknowns: false,
            drain_mode: false,
            blind_mode: false,
            had_mystery_spaces: false,
            special_modes: Vec::new(),
            original_vials: Vec::new(),
        }
    }
}
