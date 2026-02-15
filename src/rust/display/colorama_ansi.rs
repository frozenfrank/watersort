// Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
//! This module generates ANSI character codes for printing colors to terminals.
//! See: http://en.wikipedia.org/wiki/ANSI_escape_code

use std::collections::HashMap;

const CSI: &str = "\x1b[";
const OSC: &str = "\x1b]";
const BEL: &str = "\x07";

pub fn code_to_chars(code: u8) -> String {
    format!("{}{}m", CSI, code)
}

pub fn set_title(title: &str) -> String {
    format!("{}2;{}{}", OSC, title, BEL)
}

pub fn clear_screen(mode: u8) -> String {
    format!("{}{}J", CSI, mode)
}

pub fn clear_line(mode: u8) -> String {
    format!("{}{}K", CSI, mode)
}

pub struct AnsiCodes {
    codes: HashMap<&'static str, String>,
}

impl AnsiCodes {
    fn from_codes(codes: &[(&'static str, u8)]) -> Self {
        let mut map = HashMap::new();
        for &(name, code) in codes {
            map.insert(name, code_to_chars(code));
        }
        AnsiCodes { codes: map }
    }

    pub fn get(&self, name: &str) -> Option<&str> {
        self.codes.get(name).map(|s| s.as_str())
    }

    pub fn codes(&self) -> &HashMap<&'static str, String> {
        &self.codes
    }
}

impl std::ops::Index<&str> for AnsiCodes {
    type Output = str;

    fn index(&self, name: &str) -> &Self::Output {
        if let Some(fmt) = self.get(name) {
            return fmt;
        } else {
            panic!(
                "Ansi name '{}' does not exist in this struct. Use get() for a non-panic retrieval.",
                name
            );
        }
    }
}

pub struct AnsiCursor;

impl AnsiCursor {
    pub fn up(&self, n: u32) -> String {
        format!("{}{}A", CSI, n)
    }

    pub fn down(&self, n: u32) -> String {
        format!("{}{}B", CSI, n)
    }

    pub fn forward(&self, n: u32) -> String {
        format!("{}{}C", CSI, n)
    }

    pub fn back(&self, n: u32) -> String {
        format!("{}{}D", CSI, n)
    }

    pub fn pos(&self, x: u32, y: u32) -> String {
        format!("{}{};{}H", CSI, y, x)
    }
}

#[rustfmt::skip]
pub fn fore() -> AnsiCodes {
    AnsiCodes::from_codes(&[
        ("BLACK",               30),
        ("RED",                 31),
        ("GREEN",               32),
        ("YELLOW",              33),
        ("BLUE",                34),
        ("MAGENTA",             35),
        ("CYAN",                36),
        ("WHITE",               37),
        ("RESET",               39),

        // These are fairly well supported, but not part of the standard.
        ("LIGHTBLACK_EX",       90),
        ("LIGHTRED_EX",         91),
        ("LIGHTGREEN_EX",       92),
        ("LIGHTYELLOW_EX",      93),
        ("LIGHTBLUE_EX",        94),
        ("LIGHTMAGENTA_EX",     95),
        ("LIGHTCYAN_EX",        96),
        ("LIGHTWHITE_EX",       97),
    ])
}

#[rustfmt::skip]
pub fn back() -> AnsiCodes {
    AnsiCodes::from_codes(&[
        ("BLACK",               40),
        ("RED",                 41),
        ("GREEN",               42),
        ("YELLOW",              43),
        ("BLUE",                44),
        ("MAGENTA",             45),
        ("CYAN",                46),
        ("WHITE",               47),
        ("RESET",               49),

        // These are fairly well supported, but not part of the standard.
        ("LIGHTBLACK_EX",       100),
        ("LIGHTRED_EX",         101),
        ("LIGHTGREEN_EX",       102),
        ("LIGHTYELLOW_EX",      103),
        ("LIGHTBLUE_EX",        104),
        ("LIGHTMAGENTA_EX",     105),
        ("LIGHTCYAN_EX",        106),
        ("LIGHTWHITE_EX",       107),
    ])
}

#[rustfmt::skip]
pub fn style() -> AnsiCodes {
    AnsiCodes::from_codes(&[
        ("BRIGHT",              1),
        ("DIM",                 2),
        ("ITALICS",             3),
        ("UNDERSCORE",          4),
        ("INVERSE",             7),
        ("CONCEALED",           8),
        ("STRIKETHROUGH",       9),
        ("NORMAL",              22),
        ("RESET_ALL",           0),
    ])
}

pub fn cursor() -> AnsiCursor {
    AnsiCursor
}
