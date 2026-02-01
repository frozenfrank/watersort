/// Core Game structure and state management
///
/// The Game struct represents the state of a Water Sort Puzzle game.
/// It maintains a game tree structure where each Game can have a parent (prev)
/// and can spawn children. The root Game serves as the origin point.

use std::sync::{Arc};
use crate::core::color_code::COLOR_CODE_EMPTY;
use crate::core::game_settings::GameSettings;
use crate::core::{ColorCode, ColorCodeAllocator, ColorCodeExt};
use crate::types::{Completion, DepthSize, Move, Vial, VialIndex};
use crate::types::constants::{NUM_SPACES_PER_VIAL};
use crate::utils::helpers::RangeIter;


/// Represents the state of a single game configuration
///
/// Memory-efficient approach:
/// - Uses Arc for shared references to parent games (immutable)
/// - Uses Vec<Vial> for vial storage
/// - Caches num_moves and completion_order for O(1) access
/// - Stores shared settings in Arc to avoid duplication in game tree
pub struct Game {
    // Core game state
    spaces: Vec<ColorCode>,

    // Move history
    /// The move that led to this game from its parent
    last_move: Option<Move>,
    /// Reference to the parent game (None if this is root)
    prev: Option<Arc<Game>>,

    // Game statistics (cached for efficiency)
    /// Number of moves taken to reach this state
    num_moves: DepthSize,
    /// Order in which colors were completed (immutable)
    completion_order: Vec<Completion>,

    // A reference to the root game, or None if this is the root game
    root: Option<Arc<Game>>,
    settings: Arc<GameSettings>,
}

impl Game {
    /// Creates a new root game with the given vials and gameplay modes
    pub fn create(
        allocator: &mut ColorCodeAllocator,
        vials: Vec<Vial>,
        drain_mode: bool,
        blind_mode: bool,
    ) -> Arc<Game> {
        let settings = Arc::new(GameSettings {
            drain_mode,
            blind_mode,
            num_vials: vials.len() as VialIndex,
            ..Default::default()
        });

        let mut spaces: Vec<ColorCode> = Vec::with_capacity(vials.len() * NUM_SPACES_PER_VIAL);
        for vial in &vials {
            for space in vial {
                spaces.push(allocator.assign_code(space));
            }
        }

        Arc::new(Game {
            spaces,
            last_move: None,
            prev: None,
            num_moves: 0,
            completion_order: Vec::new(),
            root: None,
            settings,
        })
    }

    /// Creates a simple root game with default settings
    pub fn new_root(allocator: &mut ColorCodeAllocator, vials: Vec<Vial>) -> Arc<Game> {
        Game::create(allocator, vials, false, false)
    }

    /// Creates a new game state by applying a move to the current game
    pub fn spawn(self: &Arc<Game>, move_: Move) -> Arc<Game> {
        let mut spaces = self.spaces.clone();

        // Note: make_move would be implemented to modify spaces
        // For now, we'll leave this as a placeholder

        Arc::new(Game {
            spaces,
            settings: self.settings.clone(),
            last_move: Some(move_),
            prev: Some(Arc::clone(self)),
            num_moves: self.num_moves + 1,
            completion_order: self.completion_order.clone(),
            root: Some(if let Some(root) = self.root.clone() {root} else {self.clone()})
        })
    }

    // ============ Accessors ============

    /// Returns a reference to the vials
    pub fn get_vial_space(&self, vial_idx: usize, space_idx: usize) -> ColorCode {
        self.spaces[vial_idx as usize * NUM_SPACES_PER_VIAL + space_idx as usize]
    }

    /// Returns the number of vials
    pub fn num_vials(&self) -> usize {
        self.settings.num_vials as usize
    }

    /// Returns the number of moves to reach this state
    pub fn num_moves(&self) -> usize {
        self.num_moves as usize
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
        !self.root.is_some()
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
        for vial_idx in 0..self.num_vials() {
            let first_color = self.get_vial_space(vial_idx, 0);

            for space_idx in 0..NUM_SPACES_PER_VIAL {
                let space = self.get_vial_space(vial_idx, space_idx);
                if space.is_unknown() {
                    return false;
                }
                if space != first_color {
                    return false;
                }
            }
        }
        return true
    }

    /// Gets the top color of a vial (from top or bottom depending on drain_mode)
    pub fn get_top_vial_color(&self, vial_idx: usize, from_bottom: bool) -> ColorCode {
        for space_idx in RangeIter::new(0..NUM_SPACES_PER_VIAL, from_bottom) {
            let color = self.get_vial_space(vial_idx, space_idx);
            if color.is_unknown() {
                panic!("Watersort in Rust does not support unknown vial explorations")
            } else if color.is_empty() {
                continue
            } else {
                return color
            }
        }
        COLOR_CODE_EMPTY
    }

    // ============ Game State Validation ============

    /// Checks if a move is valid
    pub fn can_move(&self, from: usize, to: usize) -> bool {
        // Placeholder: would implement the actual move validation logic
        from != to && from < self.num_vials() && to < self.num_vials()
    }

    /// Gets the nth parent game (or None if n exceeds the depth)
    pub fn get_nth_parent(&self, n: usize) -> Option<Arc<Game>> {
        panic!("Method not implemented.")
        // let mut current = self.as_ref().cloned();
        // for _ in 1..n {
        //     if current.prev.is_none() {
        //         return None
        //     }
        //     current = current.prev;
        // }
        // current
    }
}


#[cfg(test)]
mod tests {
    use crate::core::Color;

    use super::*;

    #[test]
    fn test_game_creation() {
        let vials = [
            ['r', 'r', 'b', 'b'],
            ['g', 'g', 'y', 'y'],
        ].to_vec();

        let (_allocator, game): (ColorCodeAllocator, Arc<Game>) = new_root_from_chars(vials);
        assert_eq!(game.num_vials(), 2);
        assert_eq!(game.num_moves(), 0);
    }

    #[test]
    fn test_finished_check() {
        let vials = [
            ['r', 'r', 'r', 'r'],
            ['-', '-', '-', '-'],
        ].to_vec();

        let (_allocator, game) = new_root_from_chars(vials);
        assert!(game.is_finished());
    }


    pub fn new_root_from_chars(vials: Vec<[char; NUM_SPACES_PER_VIAL]>) -> (ColorCodeAllocator, Arc<Game>) {
        let mut allocator = ColorCodeAllocator::new();
        let vials = vials.iter().map(|vial_colors| {
            vial_colors.map(|color_char| Color(color_char.to_string()))
        }).collect();
        let game = Game::create(&mut allocator, vials, false, false);
        (allocator, game)
    }
}
