const MAX_MOVE_DEPTH: usize = 51;

/// Each index represents the game_depth at which a stat occurs.
/// The value is a counter representing the number of times this stat occurred at the depth.
pub struct MoveDepthCounter([u32; MAX_MOVE_DEPTH]);

impl MoveDepthCounter {
    pub fn increment(&mut self, mut depth: usize) {
        if depth >= MAX_MOVE_DEPTH {
            depth = MAX_MOVE_DEPTH - 1;
        }
        self.0[depth] += 1;
    }
}
