#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Play,
    Solve,
    Interact,
    Analyze,
    Quit,
    Debug,
    Unknown,
}

impl Mode {
    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "p" => Some(Mode::Play),
            "s" => Some(Mode::Solve),
            "q" => Some(Mode::Quit),
            "i" => Some(Mode::Interact),
            "a" => Some(Mode::Analyze),
            "d" => Some(Mode::Debug),
            _ => None,
        }
    }
}

impl Default for Mode {
    fn default() -> Self {
        Mode::Unknown
    }
}
