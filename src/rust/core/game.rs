use crate::core::color_code::{COLOR_CODE_EMPTY, COLOR_CODE_UNKNOWN};
use crate::core::game_settings::GameSettings;
use crate::core::{Color, ColorCode, ColorCodeExt};
use crate::types::constants::NUM_SPACES_PER_VIAL;
use crate::types::{Completion, DepthSize, Move, SpaceIndex, Vial, VialIndex};
use crate::utils::helpers::RangeIter;
use std::cell::RefCell;
use std::ops::Deref;
use std::rc::Rc;
use std::sync::Arc;
use std::fmt::{self, Formatter};

/// Represents the state of a single game configuration
///
/// Memory-efficient approach:
/// - Uses Arc for shared references to parent games (immutable)
/// - Uses Vec<Vial> for vial storage
/// - Caches num_moves and completion_order for O(1) access
/// - Stores shared settings in GameSettings to avoid duplication in game tree
#[derive(Clone)]
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
    pub settings: RefCell<GameSettings>,
}

/// Stores the result of analyzing a move
struct MoveValidityResult {
    /// Whether this move is considered valid
    valid: bool,
    /// The top color of start_vial
    start_color: ColorCode,
    /// The top color of end_vial
    end_color: ColorCode,
    /// The number of available spaces in end_vial
    end_space: VialIndex,
    /// If end_vial will be complete after this move
    will_complete: bool,
}

struct CountOnTopResult {
    is_complete: bool,
    /// Indicates whether the queried color is the only color in the vial, allowing for empty spaces as well
    only_color: bool,
    /// The number of spaces of the requested color which are accessible from the vial
    num_on_top: SpaceIndex,
    /// The number of empty spaces before any colors are found
    num_empty_spaces: SpaceIndex,
}

impl Game {
    /// Creates a new root game with the given vials and gameplay modes
    pub fn create(vials: Vec<Vial>) -> Arc<Game> {
        let mut settings = RefCell::new(GameSettings {
            num_vials: vials.len() as VialIndex,
            ..Default::default()
        });

        let allocator = &mut settings.get_mut().allocator;
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

    /// Creates a new game state by applying a move to the current game
    pub fn spawn(self: &Arc<Game>, move_: Move) -> Arc<Game> {
        let mut new_game = self.deref().clone();
        new_game.apply_move(move_.from as usize, move_.to as usize);
        Arc::new(new_game)
    }

    // ============ Accessors ============

    /// Returns a reference to the vials
    pub fn get_vial_space(&self, vial_idx: usize, space_idx: usize) -> ColorCode {
        self.spaces[vial_idx as usize * NUM_SPACES_PER_VIAL + space_idx as usize]
    }
    pub fn set_vial_space(&mut self, vial_idx: usize, space_idx: usize, color: ColorCode) {
        self.spaces[vial_idx as usize * NUM_SPACES_PER_VIAL + space_idx as usize] = color;
    }

    /// Returns the number of vials
    pub fn num_vials(&self) -> usize {
        self.settings.borrow().num_vials as usize
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
        self.root.is_none()
    }

    /// Returns the level identifier
    pub fn level(&self) -> String {
        self.settings.borrow().level.clone()
    }

    /// Returns whether this game is modified
    pub fn is_modified(&self) -> bool {
        self.settings.borrow().modified
    }

    /// Returns whether there is a color error
    pub fn has_color_error(&self) -> bool {
        self.settings.borrow().color_error
    }

    /// Returns whether there are unknown values
    pub fn has_unknowns(&self) -> bool {
        self.settings.borrow().has_unknowns
    }

    // ============ Extractors ============

    /// Retrieves the ColorCodes representing a single vial
    pub fn get_vial_code(&self, vial_idx: usize) -> [ColorCode; NUM_SPACES_PER_VIAL] {
        let start_idx = vial_idx * NUM_SPACES_PER_VIAL;
        core::array::from_fn(|i| self.spaces[start_idx+i])
    }

    /// Retrieves the interpreted Colors stored in a single vial
    pub fn get_vial_color(&self, vial_idx: usize) -> [Rc<Color>; NUM_SPACES_PER_VIAL] {
        let start_idx = vial_idx * NUM_SPACES_PER_VIAL;
        let allocator = &self.settings.borrow().allocator;
        core::array::from_fn(|i| allocator.interpret_code(self.spaces[start_idx+i]))
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
        return true;
    }

    /// Gets the top color of a vial (from top or bottom depending on drain_mode)
    pub fn get_top_vial_color(&self, vial_idx: usize, from_bottom: bool) -> ColorCode {
        for space_idx in RangeIter::new(0..NUM_SPACES_PER_VIAL, from_bottom) {
            let color = self.get_vial_space(vial_idx, space_idx);
            if color.is_unknown() {
                panic!("Watersort in Rust does not support unknown vial explorations")
            } else if color.is_empty() {
                continue;
            } else {
                return color;
            }
        }
        COLOR_CODE_EMPTY
    }

    // ============ Game State Validation ============

    /// Checks if a move is valid
    pub fn can_move(&self, start_vial: usize, end_vial: usize) -> bool {
        self.prepare_move(start_vial, end_vial).valid
    }

    fn prepare_move(&self, start_vial: usize, end_vial: usize) -> MoveValidityResult {
        let invalid_move = MoveValidityResult {
            valid: false,
            start_color: COLOR_CODE_UNKNOWN,
            end_color: COLOR_CODE_UNKNOWN,
            end_space: 0,
            will_complete: false,
        };

        if start_vial == end_vial {
            return invalid_move; // Can't move to the same place
        }
        let settings = self.settings.borrow();
        if !settings.drain_mode
            && let Some(last_move) = self.last_move
        {
            if start_vial == last_move.to as usize && end_vial == last_move.from as usize {
                return invalid_move; // Can't simply undo the previous move
            }
        }

        // Verify core game mechanics
        let start_color = self.get_top_vial_color(start_vial, settings.drain_mode);
        if start_color.is_empty() || start_color.is_unknown() {
            return invalid_move; // Can only move an active color
        }
        let end_color = self.get_top_vial_color(end_vial, false);
        if !end_color.is_empty() && end_color != start_color {
            return invalid_move; // Can only place on the same color, or an empty space
        }

        // Verify destination vial
        let end_r = self.count_on_top(end_color, end_vial, false);
        if end_r.num_empty_spaces == 0 {
            return invalid_move; // End vial is full
        }

        // Verify that this vial isn't full
        let start_r = self.count_on_top(start_color, start_vial, settings.drain_mode);
        if start_r.is_complete {
            return invalid_move; // Start is fully filled
        }
        if start_r.num_on_top > end_r.num_empty_spaces {
            // CONSIDER: We may want to allow humans to make this move, although the solver never should.
            return invalid_move; // Only move when all the spaces can be received
        }
        if end_color.is_empty()
            && (start_r.only_color || self.find_solo_vial(start_color, Some(start_vial)).is_some())
        {
            return invalid_move; // Never occupy a new container when we already have one
        }

        // Prevent rules that lead to game-play backtracks
        let mut compare_vial_fill_level = false;
        let mut require_max_solo_vial = false;

        if start_r.num_on_top == 1 && end_r.num_on_top == 1 {
            require_max_solo_vial = true;
        }

        if start_r.only_color && end_r.only_color {
            compare_vial_fill_level = true;
        } else if start_r.only_color || end_r.only_color {
            require_max_solo_vial = true;
        }

        if require_max_solo_vial {
            if let Some(max_solo_vial) = self.find_solo_vial(start_color, Some(start_vial)) {
                if end_vial != max_solo_vial {
                    // When completing a vial, never move more spaces than necessary
                    // When vacating a vial, always prefer to move into an existing "only" vial
                    // When combining vials, always move into the vial with the most spaces already
                    return invalid_move;
                }
            }
        }

        // Avoid moving a large number of squares onto a small number of squares
        // Break ties by preferring vials towards the end of the list
        if compare_vial_fill_level {
            let start_comp_val = start_r.num_on_top as f64 + (start_vial as f64 / 1000.0);
            let end_comp_val = end_r.num_on_top as f64 + (end_vial as f64 / 1000.0);
            if start_comp_val > end_comp_val {
                return invalid_move;
            }
        }

        // It's valid
        let will_complete = end_r.only_color && start_r.num_on_top == end_r.num_empty_spaces;
        MoveValidityResult {
            valid: true,
            start_color,
            end_color,
            end_space: end_r.num_empty_spaces,
            will_complete,
        }
    }

    fn count_on_top(
        &self,
        top_color: ColorCode,
        vial_idx: usize,
        from_bottom: bool,
    ) -> CountOnTopResult {
        let mut result = CountOnTopResult {
            is_complete: true,
            only_color: true,
            num_empty_spaces: 0,
            num_on_top: 0,
        };

        let mut empty_space_val: SpaceIndex = 1; // Only count empty spaces BEFORE colors
        for i in RangeIter::new(0..NUM_SPACES_PER_VIAL, from_bottom) {
            let color = self.get_vial_space(vial_idx, i);
            if color.is_empty() {
                result.num_empty_spaces += empty_space_val;
            }
            if color != top_color {
                result.is_complete = false;
                if !color.is_empty() {
                    result.only_color = false;
                    empty_space_val = 0;
                }
            } else if result.only_color {
                result.num_on_top += 1;
            }
        }

        result
    }

    /// Locates a vial that contains *only* the specified color.
    /// If multiple vials exist, returns the index with the most spaces of the specified color.
    /// If no vial exists, returns None.
    fn find_solo_vial(&self, color: ColorCode, skip_vial: Option<usize>) -> Option<usize> {
        let mut vial_index: Option<usize> = None;
        let mut spaces_in_vial: SpaceIndex = 0;
        for search_vial in 0..self.num_vials() {
            if skip_vial == Some(search_vial) {
                continue;
            }
            let CountOnTopResult {
                only_color,
                num_on_top,
                ..
            } = self.count_on_top(color, search_vial, false);
            if only_color && num_on_top > 0 {
                if vial_index.is_none() || num_on_top >= spaces_in_vial {
                    vial_index = Some(search_vial);
                    spaces_in_vial = num_on_top;
                }
            }
        }
        vial_index
    }

    fn apply_move(&mut self, start_vial: usize, end_vial: usize) -> bool {
        let move_validity = self.prepare_move(start_vial, end_vial);
        if !move_validity.valid {
            return false;
        }

        // Remove the at most end_spaces from the start vial
        let mut pieces_moved: usize = 0;
        let mut move_range: usize = move_validity.end_space as usize;
        let mut start_colors: usize = 0;

        let drain_mode = self.settings.borrow().drain_mode;

        while pieces_moved < move_range && pieces_moved < NUM_SPACES_PER_VIAL {
            let space_idx = if drain_mode {
                NUM_SPACES_PER_VIAL - pieces_moved - 1
            } else {
                pieces_moved
            };
            let color = self.get_vial_space(start_vial, space_idx);
            if color.is_empty() {
                move_range += 1;
            } else if color == move_validity.start_color {
                start_colors += 1;
                self.set_vial_space(start_vial, space_idx, COLOR_CODE_EMPTY);
            } else {
                break;
            }
            pieces_moved += 1;
        }

        // Shift down moved colors in drain mode
        if drain_mode {
            let pieces_moved = pieces_moved as isize;
            for space_idx in (0..NUM_SPACES_PER_VIAL as isize).rev() {
                let shift_from = space_idx - pieces_moved;
                let shift_color = if shift_from < 0 {
                    COLOR_CODE_EMPTY
                } else {
                    self.get_vial_space(start_vial, shift_from as usize)
                };
                self.set_vial_space(start_vial, space_idx as usize, shift_color);
            }
        }

        // Add the values back to endVial, from the bottom
        let mut space_idx = NUM_SPACES_PER_VIAL - 1;
        let mut move_range = start_colors;
        while move_range > 0 {
            let color = self.get_vial_space(end_vial, space_idx);
            if color.is_empty() {
                move_range -= 1;
                self.set_vial_space(end_vial, space_idx, move_validity.start_color);
            }
            space_idx -= 1;
            if space_idx == 0 {
                break;
            }
        }

        // Track completion order
        if move_validity.will_complete {
            todo!("self.__register_completion: {}", move_validity.end_color);
        }

        // Finish
        true
    }
}


impl std::fmt::Display for Game {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        let settings = self.settings.borrow();

        writeln!(f, "Level: {}", settings.level)?;
        writeln!(f, "Mystery: {}", settings.had_mystery_spaces)?;
        writeln!(f, "Had Unknowns: {}", settings.has_unknowns)?;
        writeln!(f, "Drain mode: {}", settings.drain_mode)?;

        for vial_idx in 0..self.num_vials() {
            let colors = self.get_vial_color(vial_idx).map(|c| c.0.clone());
            writeln!(f, "Vial {}: {}", vial_idx + 1, colors.join(" "))?;
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use crate::core::Color;

    use super::*;

    #[test]
    fn test_game_creation() {
        #[rustfmt::skip]
        let vials = [
            ['r', 'r', 'b', 'b'],
            ['g', 'g', 'y', 'y'],
        ].to_vec();

        let game= new_root_from_chars(vials);
        assert_eq!(game.num_vials(), 2);
        assert_eq!(game.num_moves(), 0);
    }

    #[test]

    fn test_finished_check() {
        #[rustfmt::skip]
        let vials = [
            ['r', 'r', 'r', 'r'],
            ['-', '-', '-', '-'],
        ].to_vec();

        let game = new_root_from_chars(vials);
        assert!(game.is_finished());
    }

    pub fn new_root_from_chars(
        vials: Vec<[char; NUM_SPACES_PER_VIAL]>,
    ) -> Arc<Game> {
        let vials = vials
            .iter()
            .map(|vial_colors| vial_colors.map(|color_char| Color(color_char.to_string())))
            .collect();
        Game::create(vials)
    }
}
