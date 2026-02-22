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
    pub fn from_str(s: &str) -> Self {
        match s {
            "p" => Mode::Play,
            "s" => Mode::Solve,
            "q" => Mode::Quit,
            "i" => Mode::Interact,
            "a" => Mode::Analyze,
            "d" => Mode::Debug,
            _ => Mode::Unknown,
        }
    }
}

impl Default for Mode {
    fn default() -> Self {
        Mode::Unknown
    }
}
