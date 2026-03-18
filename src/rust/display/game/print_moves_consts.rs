use std::sync::LazyLock;

use crate::display::{colorama_ansi::STYLE, text_formatted::TextFormatted};

pub struct PrintMovesConsts {
    pub complete: TextFormatted,
    pub vacated: TextFormatted,
    pub started: TextFormatted,
    pub max_width: usize,
}

pub static PRINT_MOVES_CONSTS: LazyLock<PrintMovesConsts> = LazyLock::new(|| {
    let complete = TextFormatted::normal(&STYLE["BRIGHT"], &"complete");
    let vacated = TextFormatted::normal(&STYLE["DIM"], &"vacated");
    let started = TextFormatted::normal(&STYLE["DIM"], &"occupied");

    let all_options = [&complete, &vacated, &started];
    let max_width = all_options.iter().map(|o| o.len_text()).max().unwrap();
    PrintMovesConsts {
        complete,
        vacated,
        started,
        max_width,
    }
});
