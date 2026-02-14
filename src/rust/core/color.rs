/// Color handling and validation for the Water Sort Puzzle

/// Represents a color in the game
#[derive(Clone, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Color {
    /// The canonical key/code for the color (e.g. "r", "m", "?")
    pub key: String,

    /// Human-friendly display name for the color (e.g. "Red", "Mint", "Blue")
    pub name: Option<&'static str>,

    /// Optional ANSI sequence for terminal rendering with a background
    pub style_primary: Option<String>,

    /// Optional ANSI sequence for terminal rendering as foreground only
    pub style_secondary: Option<String>,
}

impl Color {
    /// @deprecated Prefer Color::unknown
    pub fn new(key: &str) -> Self {
        Color::unknown(&key)
    }

    pub fn unknown(key: &str) -> Self {
        Color {
            key: key.to_string(),
            name: None,
            style_primary: None,
            style_secondary: None,
        }
    }

    pub fn known(
        key: &str,
        name: &'static str,
        style_primary: String,
        style_secondary: String,
    ) -> Self {
        Color {
            key: key.to_string(),
            name: Some(name),
            style_primary: Some(style_primary),
            style_secondary: Some(style_secondary),
        }
    }

    pub fn system(key: &str, name: &'static str, style_primary: String) -> Self {
        Color {
            key: key.to_string(),
            name: Some(name),
            style_primary: Some(style_primary),
            style_secondary: None,
        }
    }

    /// Returns true if this is a valid game color (not empty or unknown)
    pub fn is_valid(&self) -> bool {
        !self.is_reserved()
    }

    /// Returns true if this is an empty space
    pub fn is_empty(&self) -> bool {
        self.key == EMPTY_SPACE
    }

    /// Returns true if this is an unknown value
    pub fn is_unknown(&self) -> bool {
        self.key == UNKNOWN_VALUE
    }

    /// Returns true if this is a reserved value
    pub fn is_reserved(&self) -> bool {
        is_reserved(&self.key)
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
