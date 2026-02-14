use std::sync::LazyLock;
use crate::{core::Color, display::ansi::*};


#[rustfmt::skip]
pub static ALL_COLORS: LazyLock<Vec<Color>> = LazyLock::new(|| {
    vec![
        // # The actual color from the game as the background. An HSL inverted color to 20/80% Luminosity
        Color::known(&"m",  &"Mint",        ansi_back_fore(RGB(98, 214, 124),  RGB(21, 81, 34)),        ansi_fore(RGB(98, 214, 124))),
        Color::known(&"g",  &"Gray",        ansi_back_fore(RGB(99, 100, 101),  RGB(203, 204, 205)),     ansi_fore(RGB(99, 100, 101))),
        Color::known(&"o",  &"Orange",      ansi_back_fore(RGB(232, 140, 66),  RGB(91, 47, 11)),        ansi_fore(RGB(232, 140, 66))),
        Color::known(&"y",  &"Yellow",      ansi_back_fore(RGB(241, 218, 89),  RGB(94, 81, 8)),         ansi_fore(RGB(241, 218, 89))),
        Color::known(&"r",  &"Red",         ansi_back_fore(RGB(197, 42, 35),   RGB(87, 19, 15)),        ansi_fore(RGB(197, 42, 35))),
        Color::known(&"p",  &"Purple",      ansi_back_fore(RGB(115, 42, 147),  RGB(215, 176, 232)),     ansi_fore(RGB(115, 42, 147))),
        Color::known(&"pk", &"Puke",        ansi_back_fore(RGB(120, 150, 15),  RGB(228, 246, 162)),     ansi_fore(RGB(120, 150, 15))),
        Color::known(&"pn", &"Pink",        ansi_back_fore(RGB(234, 94, 123),  RGB(90, 12, 27)),        ansi_fore(RGB(234, 94, 123))),
        Color::known(&"br", &"Brown",       ansi_back_fore(RGB(126, 73, 7),    RGB(250, 209, 158)),     ansi_fore(RGB(126, 73, 7))),
        Color::known(&"lb", &"Light Blue",  ansi_back_fore(RGB(84, 163, 228),  RGB(14, 55, 88)),        ansi_fore(RGB(84, 163, 228))),
        Color::known(&"gn", &"Dark Green",  ansi_back_fore(RGB(17, 101, 51),   RGB(124, 233, 168)),     ansi_fore(RGB(17, 101, 51))),
        Color::known(&"b",  &"Blue",        ansi_back_fore(RGB(58, 46, 195),   RGB(197, 193, 240)),     ansi_fore(RGB(58, 46, 195))),
    ]
});
