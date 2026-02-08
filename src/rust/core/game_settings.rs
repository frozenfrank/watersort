use crate::{core::ColorCodeAllocator, types::VialIndex};

/// Shared global settings for a game tree
/// Stored once on the root game to avoid duplication
#[derive(Clone)]
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
    /// Required to reinterpret the color codes in the game
    pub allocator: ColorCodeAllocator,
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
            allocator: ColorCodeAllocator::new(),
        }
    }
}

impl std::fmt::Debug for GameSettings {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("GameSettings")
            .field("level", &self.level)
            .field("num_vials", &self.num_vials)
            .field("modified", &self.modified)
            .field("color_error", &self.color_error)
            .field("has_unknowns", &self.has_unknowns)
            .field("drain_mode", &self.drain_mode)
            .field("blind_mode", &self.blind_mode)
            .field("had_mystery_spaces", &self.had_mystery_spaces)
            .field("allocator", &"<allocator>")
            .finish()
    }
}
