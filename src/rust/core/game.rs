/// Core Game structure and state management
///
/// The Game struct represents the state of a Water Sort Puzzle game.
/// It maintains a game tree structure where each Game can have a parent (prev)
/// and can spawn children. The root Game serves as the origin point.

use std::sync::Arc;
use crate::types::{Move, Completion, Vial};
use crate::types::constants::{NUM_SPACES_PER_VIAL};
use crate::core::color::{EMPTY_SPACE, UNKNOWN_VALUE};

/// Shared global settings for a game tree
/// Stored once on the root game to avoid duplication
#[derive(Debug, Clone)]
pub struct GameSettings {
    /// The level identifier (e.g., "263")
    pub level: String,
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
}

impl Default for GameSettings {
    fn default() -> Self {
        GameSettings {
            level: String::new(),
            modified: false,
            color_error: false,
            has_unknowns: false,
            drain_mode: false,
            blind_mode: false,
            had_mystery_spaces: false,
        }
    }
}

/// Represents the state of a single game configuration
///
/// Memory-efficient approach:
/// - Uses Arc for shared references to parent games (immutable)
/// - Uses Vec<Vial> for vial storage
/// - Caches num_moves and completion_order for O(1) access
/// - Stores shared settings in Arc to avoid duplication in game tree
pub struct Game {
    // Core game state
    vials: Vec<Vial>,

    // Move history
    /// The move that led to this game from its parent
    last_move: Option<Move>,
    /// Reference to the parent game (None if this is root)
    prev: Option<Arc<Game>>,

    // Game statistics (cached for efficiency)
    /// Number of moves taken to reach this state
    num_moves: usize,
    /// Order in which colors were completed (immutable)
    completion_order: Vec<Completion>,

    // Shared settings (Arc is cheap to clone)
    settings: Arc<GameSettings>,

    // Whether this is the root game
    is_root: bool,
}

impl Game {
    /// Creates a new root game with the given vials and gameplay modes
    pub fn create(
        vials: Vec<Vial>,
        drain_mode: bool,
        blind_mode: bool,
    ) -> Arc<Self> {
        let settings = Arc::new(GameSettings {
            drain_mode,
            blind_mode,
            ..Default::default()
        });

        Arc::new(Game {
            vials,
            last_move: None,
            prev: None,
            num_moves: 0,
            completion_order: Vec::new(),
            settings,
            is_root: true,
        })
    }

    /// Creates a simple root game with default settings
    pub fn new_root(vials: Vec<Vial>) -> Arc<Game> {
        Game::create(vials, false, false)
    }
    /// Creates a new game state by applying a move to the current game
    pub fn spawn(self: &Arc<Game>, move_: Move) -> Arc<Game> {
        let new_vials = self.vials.clone();

        // Note: make_move would be implemented to modify new_vials
        // For now, we'll leave this as a placeholder

        Arc::new(Game {
            vials: new_vials,
            last_move: Some(move_),
            prev: Some(Arc::clone(self)),
            num_moves: self.num_moves + 1,
            completion_order: self.completion_order.clone(),
            settings: Arc::clone(&self.settings),
            is_root: false,
        })
    }

    // ============ Accessors ============

    /// Returns a reference to the vials
    pub fn vials(&self) -> &[Vial] {
        &self.vials
    }

    /// Returns the number of vials
    pub fn num_vials(&self) -> usize {
        self.vials.len()
    }

    /// Returns the number of moves to reach this state
    pub fn num_moves(&self) -> usize {
        self.num_moves
    }

    /// Returns the order of color completions
    pub fn completion_order(&self) -> &[Completion] {
        &self.completion_order
    }

    /// Returns the last move applied to reach this state
    pub fn last_move(&self) -> Option<Move> {
        self.last_move
    }

    /// Returns a reference to the parent game, if any
    pub fn prev(&self) -> Option<&Arc<Game>> {
        self.prev.as_ref()
    }

    /// Returns whether this is the root game
    pub fn is_root(&self) -> bool {
        self.is_root
    }

    /// Returns the level identifier
    pub fn level(&self) -> &str {
        &self.settings.level
    }

    /// Returns whether this game is modified
    pub fn is_modified(&self) -> bool {
        self.settings.modified
    }

    /// Returns whether there is a color error
    pub fn has_color_error(&self) -> bool {
        self.settings.color_error
    }

    /// Returns whether there are unknown values
    pub fn has_unknowns(&self) -> bool {
        self.settings.has_unknowns
    }

    /// Returns the game modes active in this game
    pub fn special_modes(&self) -> Vec<&'static str> {
        let mut modes = Vec::new();
        if self.settings.drain_mode {
            modes.push("drain");
        }
        if self.settings.blind_mode {
            modes.push("blind");
        }
        if self.settings.had_mystery_spaces {
            modes.push("mystery");
        }
        modes
    }

    // ============ Game State Queries ============

    /// Returns true if all vials are completed (all spaces in each vial are the same color)
    pub fn is_finished(&self) -> bool {
        for vial in &self.vials {
            // Check if all non-empty spaces have the same color
            let mut first_color: Option<char> = None;

            for &space in vial {
                if space == EMPTY_SPACE {
                    continue;
                }
                if space == UNKNOWN_VALUE {
                    return false;  // Unknown value means not finished
                }
                match first_color {
                    None => first_color = Some(space),
                    Some(color) if color != space => return false,
                    _ => continue,
                }
            }
        }
        true
    }

    /// Gets the color at a specific position
    pub fn get_color(&self, vial_idx: usize, space_idx: usize) -> Option<char> {
        self.vials.get(vial_idx)
            .and_then(|vial: &Vial| vial.get(space_idx))
            .copied()
    }

    /// Gets the top color of a vial (from top or bottom depending on drain_mode)
    pub fn get_top_vial_color(&self, vial_idx: usize, from_bottom: bool) -> Option<char> {
        let vial = self.vials.get(vial_idx)?;
        let range: Box<dyn Iterator<Item = usize>> = if from_bottom {
            Box::new((0..NUM_SPACES_PER_VIAL).rev())
        } else {
            Box::new(0..NUM_SPACES_PER_VIAL)
        };

        for i in range {
            let color = vial[i];
            match color {
                EMPTY_SPACE => continue,
                _ => return Some(color),
            }
        }
        None
    }

    // ============ Game State Validation ============

    /// Checks if a move is valid
    pub fn can_move(&self, from: usize, to: usize) -> bool {
        // Placeholder: would implement the actual move validation logic
        from != to && from < self.num_vials() && to < self.num_vials()
    }

    /// Gets the nth parent game (or None if n exceeds the depth)
    pub fn get_nth_parent(&self, n: usize) -> Option<Arc<Game>> {
        let mut current = self.prev.as_ref().cloned();
        for _ in 1..n {
            current = current.and_then(|g| g.prev.as_ref().cloned());
        }
        current
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_game_creation() {
        let vial1: Vial = ['r', 'r', 'b', 'b'];
        let vial2: Vial = ['g', 'g', 'y', 'y'];
        let vials = vec![vial1, vial2];

        let game = Game::new_root(vials);
        assert_eq!(game.num_vials(), 2);
        assert_eq!(game.num_moves(), 0);
    }

    #[test]
    fn test_finished_check() {
        let completed_vial: Vial = ['r', 'r', 'r', 'r'];
        let empty_vial: Vial = ['-', '-', '-', '-'];
        let vials = vec![completed_vial, empty_vial];

        let game = Game::new_root(vials);
        assert!(game.is_finished());
    }
}
