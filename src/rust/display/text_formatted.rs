use crate::display::colorama_ansi::STYLE;

#[derive(Debug, Default, Clone)]
pub struct TextFormatted {
    str: String,
    text_len: usize,
}

impl TextFormatted {
    pub fn normal(format: &str, text: &str) -> Self {
        let mut out = Self::default();
        out.push_text_normal(format, text);
        out
    }

    fn push_raw_format(&mut self, pre_format: &str, text: &str, post_format: &str) {
        self.push_fmt(pre_format);
        self.push_text(text);
        self.push_fmt(post_format);
    }

    pub fn push_text_reset(&mut self, pre_format: &str, text: &str) {
        self.push_raw_format(pre_format, text, &STYLE["RESET_ALL"]);
    }

    pub fn push_text_normal(&mut self, pre_format: &str, text: &str) {
        self.push_raw_format(pre_format, text, &STYLE["NORMAL"]);
    }

    pub fn push_text(&mut self, text: &str) {
        self.text_len += text.len();
        self.str.push_str(text);
    }

    pub fn push_fmt(&mut self, format: &str) {
        self.str.push_str(format);
    }

    pub fn concat(&mut self, other: &Self) {
        self.text_len += other.text_len;
        self.str.push_str(&other.str);
    }

    pub fn left_justify(&mut self, min_width_text: usize) {
        while self.text_len < min_width_text {
            self.text_len += 1;
            self.str.push(' ');
        }
    }

    pub fn len_chars(&self) -> usize {
        self.str.len()
    }

    pub fn len_text(&self) -> usize {
        self.text_len
    }

    pub fn as_str(&self) -> &str {
        &self.str
    }
}

impl std::fmt::Display for TextFormatted {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.str.fmt(f)
    }
}
