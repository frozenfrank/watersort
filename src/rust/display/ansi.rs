use std::fmt::Write;

const ANSI_ESCAPE: &str = "\x1b[";

pub struct RGB(pub u8,pub  u8,pub u8);

const ANSI_COLOR_LEN: usize = 20;

// Helper functions to generate ANSI escape sequences
fn ansi_fore_s(rgb: RGB, s: &mut String) {
    let RGB (r, g, b) = rgb;
    write!(s, "{ANSI_ESCAPE}38;2;{r};{g};{b}m");
}

fn ansi_back_s(rgb: RGB, s: &mut String) {
    let RGB (r, g, b) = rgb;
    write!(s, "{ANSI_ESCAPE}48;2;{r};{g};{b}m");
}

pub fn ansi_fore(rgb: RGB) -> String {
    let mut s = String::with_capacity(ANSI_COLOR_LEN);
    ansi_fore_s(rgb, &mut s);
    s
}

pub fn ansi_back(rgb: RGB) -> String {
    let mut s = String::with_capacity(ANSI_COLOR_LEN);
    ansi_back_s(rgb, &mut s);
    s
}

pub fn ansi_back_fore(back_rgb: RGB, fore_rgb: RGB) -> String {
    let mut s = String::with_capacity(ANSI_COLOR_LEN*2);
    ansi_back_s(back_rgb, &mut s);
    ansi_fore_s(fore_rgb, &mut s);
    s
}
