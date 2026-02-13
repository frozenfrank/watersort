/// Color handling and validation for the Water Sort Puzzle

/// Represents a color in the game
#[derive(Clone, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Color {
    /// The canonical key/code for the color (e.g. "r", "m", "?")
    pub key: String,

    /// Short code (mirrors `key` for now) reserved for compatibility
    pub code: String,

    /// Optional ANSI background sequence for terminal rendering
    pub ansi_back: Option<String>,

    /// Optional ANSI foreground sequence for terminal rendering
    pub ansi_fore: Option<String>,

    /// Human-friendly display name for the color (e.g. "Red")
    pub display_name: Option<String>,

    /// Whether this color is reserved (empty/unknown)
    pub reserved: bool,
}

impl Color {
    pub fn new(name: &str) -> Self {
        let key = name.to_string();
        Color {
            key: key.clone(),
            code: key.clone(),
            ansi_back: None,
            ansi_fore: None,
            display_name: None,
            reserved: is_reserved(&key),
        }
    }

    /// Returns true if this is a valid game color (not empty or unknown)
    pub fn is_valid(&self) -> bool {
        !self.reserved
    }

    /// Returns true if this is an empty space
    pub fn is_empty(&self) -> bool {
        self.key == EMPTY_SPACE
    }

    /// Returns true if this is an unknown value
    pub fn is_unknown(&self) -> bool {
        self.key == UNKNOWN_VALUE
    }

    pub fn is_reserved(&self) -> bool {
        self.reserved
    }

    /// Returns the canonical key/code for this color
    pub fn key(&self) -> &str {
        &self.key
    }

    /// Returns the short code for this color (same as key)
    pub fn code(&self) -> &str {
        &self.code
    }

    /// Optional ANSI background for pretty printing
    pub fn ansi_back(&self) -> Option<&str> {
        self.ansi_back.as_deref()
    }

    /// Optional ANSI foreground for pretty printing
    pub fn ansi_fore(&self) -> Option<&str> {
        self.ansi_fore.as_deref()
    }

    /// Optional human-friendly display name
    pub fn display_name(&self) -> Option<&str> {
        self.display_name.as_deref()
    }
}

impl std::fmt::Debug for Color {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.key)
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
        let red = Color::new("r");
        assert!(red.is_valid());
        assert!(!red.is_empty());
        assert!(!red.is_unknown());

        let empty = Color::new("-");
        assert!(!empty.is_valid());
        assert!(empty.is_empty());

        let unknown = Color::new("?");
        assert!(!unknown.is_valid());
        assert!(unknown.is_unknown());
    }
}
