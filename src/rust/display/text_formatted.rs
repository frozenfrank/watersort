use crate::display::colorama_ansi::STYLE;

#[derive(Debug, Default)]
pub struct TextFormatted {
    str: String,
    text_len: usize,
}

impl TextFormatted {
    fn push_raw_format(&mut self, pre_format: &str, text: &str, post_format: &str) {
        self.push_fmt(pre_format);
        self.push_text(text);
        self.push_fmt(post_format);
    }

    pub fn push_reset_format(&mut self, pre_format: &str, text: &str) {
        self.push_raw_format(pre_format, text, &STYLE["RESET_ALL"]);
    }

    pub fn push_text(&mut self, text: &str) {
        self.text_len += text.len();
        self.str.push_str(text);
    }

    pub fn push_fmt(&mut self, format: &str) {
        self.str.push_str(format);
    }

    pub fn len_chars(&self) -> usize {
        self.str.len()
    }

    pub fn len_text(&self) -> usize {
        self.text_len
    }
}

impl std::fmt::Display for TextFormatted {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.str.fmt(f)
    }
}
