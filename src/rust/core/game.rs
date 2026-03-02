use crate::core::color_code::{COLOR_CODE_EMPTY, COLOR_CODE_UNKNOWN};
use crate::core::game_settings::GameSettings;
use crate::core::{Color, ColorCode, ColorCodeAllocator, ColorCodeExt};
use crate::types::{Completion, DepthSize, Move, SpaceIndex, Vial, VialIndex};
use crate::utils::helpers::RangeIter;
use crate::{MoveInfo, NUM_SPACES_PER_VIAL};
use itertools::Itertools;
use std::borrow::Cow;
use std::cell::RefCell;
use std::fmt::{self, Debug, Formatter};
use std::ops::Deref;
use std::rc::Rc;
use std::sync::Arc;

/// Represents the state of a single game configuration
///
/// Memory-efficient approach:
/// - Uses Arc for shared references to parent games (immutable)
/// - Uses Vec<Vial> for vial storage
/// - Caches num_moves and completion_order for O(1) access
/// - Stores shared settings in GameSettings to avoid duplication in game tree
#[derive(Clone, Eq)]
pub struct Game<'a> {
    // Core game state
    spaces: Vec<ColorCode>,

    // Move history
    /// The move that led to this game from its parent
    last_move: Option<Move>,
    /// Reference to the parent game (None if this is root)
    prev: Option<Arc<Game<'a>>>,

    // Game statistics (cached for efficiency)
    /// Number of moves taken to reach this state
    num_moves: DepthSize,
    /// Order in which colors were completed (immutable)
    completion_order: Cow<'a, Vec<Completion>>,

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

impl<'a> Game<'a> {
    /// Creates a new game with the given vials
    pub fn create(vials: Vec<Vial>) -> Game<'a> {
        let settings = GameSettings {
            num_vials: vials.len() as VialIndex,
            ..Default::default()
        };

        Game::create_with_settings(vials, settings)
    }

    /// Creates a new game with the given vials in a bare ColorCodeAllocator
    pub fn create_bare(vials: Vec<Vial>) -> Game<'a> {
        let settings = GameSettings {
            num_vials: vials.len() as VialIndex,
            allocator: ColorCodeAllocator::new_bare(),
            ..Default::default()
        };

        Game::create_with_settings(vials, settings)
    }

    pub fn create_sibling_game(vials: Vec<Vial>, sibling: &Game) -> Game<'a> {
        let settings = sibling.settings.borrow().clone();
        Game::create_with_settings(vials, settings)
    }

    fn create_with_settings(vials: Vec<Vial>, settings: GameSettings) -> Game<'a> {
        let mut settings = RefCell::new(settings);
        let allocator = &mut settings.get_mut().allocator;

        let mut spaces: Vec<ColorCode> = Vec::with_capacity(vials.len() * NUM_SPACES_PER_VIAL);
        for vial in &vials {
            for space in vial {
                spaces.push(allocator.assign_code(space));
            }
        }

        Game {
            spaces,
            last_move: None,
            prev: None,
            num_moves: 0,
            completion_order: Cow::Owned(Vec::new()),
            settings,
        }
    }

    pub fn new_root(vials: Vec<Vial>) -> Arc<Game<'static>> {
        Arc::new(Game::create(vials))
    }

    pub fn new_root_bare(vials: Vec<Vial>) -> Arc<Game<'static>> {
        Arc::new(Game::create_bare(vials))
    }

    /// Creates a new game state by applying a move to the current game
    pub fn spawn(self: &Arc<Game<'a>>, move_: Move) -> Arc<Game<'a>> {
        // SAFETY: The parent game is kept alive by the Arc in `prev`, and the
        // parent game recursively references the Owned completion order, so the
        // borrowed reference will remain valid for the entire lifetime of this game.
        let completion_order = unsafe {
            std::mem::transmute::<Cow<'_, Vec<Completion>>, Cow<'a, Vec<Completion>>>(
                Cow::Borrowed(&self.completion_order),
            )
        };

        let mut new_game: Game<'a> = Game {
            completion_order,
            prev: Some(self.clone()),
            spaces: self.spaces.clone(),
            last_move: Some(move_),
            num_moves: self.num_moves,
            settings: self.settings.clone(),
        };
        new_game.apply_move(move_.from as usize, move_.to as usize);
        Arc::new(new_game)
    }

    pub fn generate_next_games(self: &Arc<Game<'a>>) -> Vec<Arc<Game<'a>>> {
        self.generate_next_moves()
            .into_iter()
            .map(|m| self.spawn(m))
            .collect()
    }
    pub fn generate_next_moves(&self) -> Vec<Move> {
        // CONSIDER using a static MAX_NUM_VIALS and allocating on the stack instead of the heap.
        let num_vials = self.num_vials();
        let mut moves = Vec::with_capacity(num_vials);

        #[derive(Clone, Copy)]
        struct Vial {
            empty_valid: bool,
            move_valid: bool,
        }

        impl Default for Vial {
            fn default() -> Self {
                Self {
                    empty_valid: true,
                    move_valid: true,
                }
            }
        }

        let mut vials = vec![Vial::default(); num_vials];

        for (start, end) in (0..num_vials).cartesian_product(0..num_vials) {
            if !vials[start].move_valid {
                continue;
            }

            let MoveValidityResult {
                valid,
                end_color,
                will_complete,
                ..
            } = self.prepare_move(start, end);
            if !valid {
                continue;
            }

            // Only allow the first move into an empty vial from a given start vial
            if end_color.is_empty() {
                if vials[start].empty_valid {
                    vials[start].empty_valid = false;
                } else {
                    continue;
                }
            } else if will_complete {
                // If there is a move that will complete a color in a vial, then moving from that vial
                // is never valid. Either, it would attempt to complete the other direction OR  it would
                // only move into an empty vial. Obviously, there are no other colors for it to land on.
                vials[end].move_valid = false;
            }

            // Fine, it's valid
            moves.push(Move::new(start, end));
        }

        moves
    }

    pub fn to_arc(self: Game<'a>) -> Arc<Game<'a>> {
        Arc::new(self)
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

    /// Returns the number of moves applied to the root to get to this game
    pub fn get_depth(&self) -> usize {
        self.num_moves as usize
    }

    /// Returns a reference to the parent game, if any
    pub fn prev(&self) -> Option<&Arc<Game<'_>>> {
        self.prev.as_ref()
    }

    /// Returns whether this is the root game
    pub fn is_root(&self) -> bool {
        self.num_moves == 0
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
        core::array::from_fn(|i| self.spaces[start_idx + i])
    }

    /// Retrieves the interpreted Colors stored in a single vial
    pub fn get_vial_color(&self, vial_idx: usize) -> [Rc<Color>; NUM_SPACES_PER_VIAL] {
        let start_idx = vial_idx * NUM_SPACES_PER_VIAL;
        let allocator = &self.settings.borrow().allocator;
        core::array::from_fn(|i| allocator.interpret_code(self.spaces[start_idx + i]))
    }

    /// Returns an array of NUM_SPACES_PER_VIAL * num_vials ColorCodes, in vial-major order.
    pub fn get_spaces_code(&self) -> &[ColorCode] {
        &self.spaces
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
        for color in RangeIter::new(self.get_vial_code(vial_idx).into_iter(), from_bottom) {
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

    pub fn get_move_info(&self) -> Option<MoveInfo> {
        if self.last_move.is_none() {
            return None; // Also guarantees the presence of `prev`
        }
        let Move { from, to } = self.last_move.unwrap();
        let start = from as usize;
        let end = to as usize;

        let settings = self.settings.borrow();
        let drain_mode = settings.drain_mode;
        let num_spaces_per_vial = NUM_SPACES_PER_VIAL as u8;

        // Look up colors & quantities moved
        let color_moved = self.get_top_vial_color(end, false); // The color is always the one on top, even in drain mode
        let prev_game = self.prev.as_deref().unwrap();
        let CountOnTopResult {
            num_on_top: num_moved,
            num_empty_spaces: start_empty_spaces,
            ..
        } = prev_game.count_on_top(color_moved, start, drain_mode);
        let CountOnTopResult {
            is_complete,
            num_empty_spaces: end_empty_spaces,
            ..
        } = self.count_on_top(color_moved, end, drain_mode);

        // Prepare and return
        let color_moved = settings.allocator.interpret_code(color_moved);
        let vacated_vial = num_moved + start_empty_spaces == num_spaces_per_vial;
        let started_vial = num_spaces_per_vial - num_moved == end_empty_spaces;
        Some(MoveInfo {
            color_moved,
            num_moved,
            is_complete,
            vacated_vial,
            started_vial,
        })
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

    pub fn apply_move(&mut self, start_vial: usize, end_vial: usize) -> bool {
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
            if space_idx == 0 {
                break;
            }
            space_idx -= 1;
        }

        // Track completion order
        if move_validity.will_complete {
            self.register_completion(move_validity.end_color);
        }

        // Finish
        self.num_moves += 1;
        true
    }

    fn register_completion(&mut self, completing_color: ColorCode) {
        let mut completions = self.completion_order.deref().clone();
        completions.push(Completion {
            color: completing_color,
            depth: self.num_moves,
        });
        self.completion_order = Cow::Owned(completions);
    }
}

impl PartialEq for Game<'_> {
    fn eq(&self, other: &Self) -> bool {
        self.spaces == other.spaces && RefCell::eq(&self.settings, &other.settings)
    }
}

impl std::hash::Hash for Game<'_> {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.spaces.hash(state);
    }
}

impl std::fmt::Display for Game<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        let settings = self.settings.borrow();

        writeln!(f, "Level: {}", settings.level)?;
        writeln!(f, "Mystery: {}", settings.had_mystery_spaces)?;
        writeln!(f, "Had Unknowns: {}", settings.has_unknowns)?;
        writeln!(f, "Drain mode: {}", settings.drain_mode)?;

        for vial_idx in 0..self.num_vials() {
            let colors = self.get_vial_color(vial_idx).map(|c| c.key.clone());
            writeln!(f, "Vial {}: {}", vial_idx + 1, colors.join(" "))?;
        }

        Ok(())
    }
}

impl std::fmt::Debug for Game<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        f.debug_struct("Game")
            .field("spaces", &self.spaces)
            .field("last_move", &self.last_move)
            .field("num_moves", &self.num_moves)
            .field("completion_order", &self.completion_order)
            .field("settings", &"<settings>")
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashSet;

    use crate::core::Color;

    use super::*;

    #[test]
    fn test_game_creation() {
        #[rustfmt::skip]
        let vials = [
            ['r', 'r', 'b', 'b'],
            ['g', 'g', 'y', 'y'],
        ].to_vec();

        let game = new_root_from_chars(vials);
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

    #[test]
    fn test_move_correctness() {
        #[rustfmt::skip]
        let vials1 = [
            ['-', '-', 'r', 'r'],
            ['-', '-', 'r', 'r'],
            ['b', 'b', 'b', 'b'],
        ].to_vec();

        #[rustfmt::skip]
        let vials2 = [
            ['-', '-', '-', '-'],
            ['r', 'r', 'r', 'r'],
            ['b', 'b', 'b', 'b'],
        ].to_vec();

        let mut game1 = new_root_from_chars(vials1);
        game1.apply_move(0, 1);

        let game2 = Game::create_sibling_game(vec_to_vials(vials2), &game1);

        assert_eq!(game1, game2);
    }

    #[test]
    fn test_completion_order_address_stability() {
        #[rustfmt::skip]
        let vials = [
            ['r', 'r', 'b', 'b'],
            ['b', 'b', 'r', 'r'],
            ['-', '-', '-', '-'],
        ].to_vec();

        let mut game = new_root_from_chars(vials);
        let initial_completion_ptr = game.completion_order.as_ptr();

        game.apply_move(1, 2);
        let after_first_move_ptr = game.completion_order.as_ptr();

        game.apply_move(1, 0);
        let after_second_move_ptr = game.completion_order.as_ptr();

        assert_eq!(
            initial_completion_ptr, after_first_move_ptr,
            "Completion order address changed after first move"
        );
        assert_eq!(
            initial_completion_ptr, after_second_move_ptr,
            "Completion order address changed after second move"
        );
    }

    #[test]
    fn test_completion_order_address_stability_spawning() {
        #[rustfmt::skip]
        let vials = [
            ['r', 'r', 'b', 'b'],
            ['b', 'b', 'r', 'r'],
            ['-', '-', '-', '-'],
        ].to_vec();

        let game1 = Arc::new(new_root_from_chars(vials));
        println!("{}", game1);

        let game2 = game1.spawn(Move::vials(2, 3)); // Move blue
        println!("{}", game2);
        assert_ne!(
            Arc::as_ptr(&game1),
            Arc::as_ptr(&game2),
            "Game2 should allocation to a new location"
        );
        assert_eq!(
            game1.completion_order.as_ptr(),
            game2.completion_order.as_ptr(),
            "Game2 should reference the same completion vector"
        );

        let game3 = game2.spawn(Move::vials(1, 2)); // Complete red
        println!("{}", game3);
        assert_ne!(
            Arc::as_ptr(&game2),
            Arc::as_ptr(&game3),
            "Game3 should allocation to a new location"
        );
        assert_ne!(
            game2.completion_order.as_ptr(),
            game3.completion_order.as_ptr(),
            "Game3 should reference a new completion vector"
        );

        let game4 = game3.spawn(Move::vials(1, 3)); // Complete blue
        println!("{}", game4);
        assert_ne!(
            Arc::as_ptr(&game3),
            Arc::as_ptr(&game4),
            "Game4 should allocation to a new location"
        );
        assert_ne!(
            game3.completion_order.as_ptr(),
            game4.completion_order.as_ptr(),
            "Game4 should reference a new completion vector"
        );
    }

    #[test]
    fn test_completion_order_unique_count() {
        #[rustfmt::skip]
        let vials = [ // Level 100
            ['m', 'g', 'o', 'y'],
            ['r', 'p', 'k', 'l'], // k = pk
            ['k', 'n', 'm', 'p'],
            ['y', 'n', 'r', 'i'], // i = br
            ['k', 'b', 'i', 'p'],
            ['k', 'g', 'p', 'y'],
            ['o', 'g', 'l', 'e'], // e = dg
            ['r', 'e', 'l', 'n'], // l = lb
            ['b', 'b', 'l', 'm'],
            ['e', 'i', 'n', 'o'],
            ['g', 'm', 'y', 'o'],
            ['r', 'i', 'e', 'b'],
            ['-', '-', '-', '-'],
            ['-', '-', '-', '-'],
        ].to_vec();

        #[rustfmt::skip]
        let moves = [
            Move::vials(7, 13),   //  (1 o occupied)
            Move::vials(5, 14),   //  (1 pk occupied)
            Move::vials(6, 14),   //  (1 pk)
            Move::vials(3, 14),   //  (1 pk)
            Move::vials(11, 7),   //  (1 g)
            Move::vials(1, 11),   //  (1 m)
            Move::vials(1, 6),    //  (1 g)
            Move::vials(1, 13),   //  (1 o)
            Move::vials(4, 1),    //  (1 y)
            Move::vials(4, 3),    //  (1 pn)
            Move::vials(12, 4),   //  (1 r)
            Move::vials(8, 4),    //  (1 r)
            Move::vials(10, 8),   //  (1 dg)
            Move::vials(10, 12),  //  (1 br)
            Move::vials(3, 10),   //  (2 pn)
            Move::vials(11, 3),   //  (2 m)
            Move::vials(1, 11),   //  (2 y vacated)
            Move::vials(9, 1),    //  (2 b occupied)
            Move::vials(5, 1),    //  (1 b)
            Move::vials(12, 5),   //  (2 br)
            Move::vials(8, 12),   //  (2 dg)
            Move::vials(8, 9),    //  (1 lb)
            Move::vials(10, 8),   //  (3 pn complete)
            Move::vials(10, 13),  //  (1 o vacated)
            Move::vials(2, 10),   //  (1 r occupied)
            Move::vials(4, 10),   //  (3 r complete)
            Move::vials(5, 4),    //  (3 br complete)
            Move::vials(2, 5),    //  (1 p)
            Move::vials(2, 14),   //  (1 pk complete)
            Move::vials(9, 2),    //  (2 lb)
            Move::vials(3, 9),    //  (3 m complete)
            Move::vials(3, 5),    //  (1 p vacated)
            Move::vials(7, 3),    //  (2 g occupied)
            Move::vials(7, 2),    //  (1 lb complete)
            Move::vials(12, 7),   //  (3 dg complete)
            Move::vials(6, 3),    //  (2 g complete)
            Move::vials(6, 5),    //  (1 p complete)
            Move::vials(11, 6),   //  (3 y complete)
            Move::vials(11, 13),  //  (1 o complete)
            Move::vials(12, 1),   //  (1 b complete)
        ];

        let num_colors = vials.len() - 2;
        let mut completions = HashSet::<*const Completion>::with_capacity(vials.len());
        let mut game = Game::new_root_bare(vec_to_vials(vials));
        let mut prev_depth = usize::MAX;

        assert_eq!(
            num_colors,
            game.settings.borrow().allocator.num_colors(),
            "Game should have as many colors as full vials"
        );

        for move_ in moves {
            game = game.spawn(move_);

            print!("D: {} ", game.get_depth());
            print!("Completion Addr: {:p} ", game.completion_order.as_ptr());
            print!("Completions Len: {:} ", game.completion_order.len());
            // print!("Completions: {:?} ", game.completion_order);
            // print!("V: {:?} ", game.get_spaces_color());

            // if let Some(prev) = game.prev.as_ref() {
            //     print!("\tMove: {:}", move_);

            //     let start_vial = prev.get_vial_color(move_.from as usize);
            //     let end_vial = prev.get_vial_color(move_.to as usize);
            //     print!("\tBefore: {:?} -> {:?} ", start_vial, end_vial);

            //     let start_vial = game.get_vial_color(move_.from as usize);
            //     let end_vial = game.get_vial_color(move_.to as usize);
            //     print!("\tAfter: {:?} -> {:?} ", start_vial, end_vial);
            // }

            if game.get_depth() == prev_depth {
                print!("No change! ");
            }

            println!("");
            prev_depth = game.get_depth();
            completions.insert(game.completion_order.as_ptr());
        }

        assert_eq!(
            moves.len(),
            game.get_depth(),
            "The final game should include all scheduled moves"
        );
        assert_eq!(
            num_colors + 1,
            completions.len(),
            "There should be 13 unique completions (1 for the blank state, and 12 unique ones for each completion)"
        );

        println!("{:#?}", game.completion_order);
    }

    fn vec_to_vials(vials: Vec<[char; NUM_SPACES_PER_VIAL]>) -> Vec<Vial> {
        vials
            .iter()
            .map(|vial_colors| {
                vial_colors.map(|color_char| Color::unknown(&color_char.to_string()))
            })
            .collect()
    }

    pub fn new_root_from_chars(vials: Vec<[char; NUM_SPACES_PER_VIAL]>) -> Game<'static> {
        Game::create(vec_to_vials(vials))
    }
}
