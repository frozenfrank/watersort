/// Color handling and validation for the Water Sort Puzzle


/// Represents a color in the game
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Color<'a>(pub &'a str);

impl<'a> Color<'a> {
    pub fn new(name: &'a str) -> Self {
        Color(&name)
    }

    /// Returns true if this is a valid game color (not empty or unknown)
    pub fn is_valid(&self) -> bool {
        !self.is_reserved()
    }

    /// Returns true if this is an empty space
    pub fn is_empty(&self) -> bool {
        self.0 == EMPTY_SPACE
    }

    /// Returns true if this is an unknown value
    pub fn is_unknown(&self) -> bool {
        self.0 == UNKNOWN_VALUE
    }

    pub fn is_reserved(&self) -> bool {
      is_reserved(self.0)
    }
}

/// Special character representing an empty space in a vial
pub const EMPTY_SPACE: &'static str = "-";

/// Special character representing an unknown/mystery value
pub const UNKNOWN_VALUE: &'static str = "?";

/// Reserved colors that have special meanings in the game
pub const RESERVED_COLORS: &[&str] = &[EMPTY_SPACE, UNKNOWN_VALUE];

/// Validates that a color character is acceptable
pub fn is_reserved(ch: &str) -> bool {
    RESERVED_COLORS.contains(&ch)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_color_validation() {
        let red = Color("r");
        assert!(red.is_valid());
        assert!(!red.is_empty());
        assert!(!red.is_unknown());

        let empty = Color("-");
        assert!(!empty.is_valid());
        assert!(empty.is_empty());

        let unknown = Color("?");
        assert!(!unknown.is_valid());
        assert!(unknown.is_unknown());
    }
}
