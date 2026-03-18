pub type ColorCode = u8;

pub const COLOR_CODE_EMPTY: ColorCode = 0;
pub const COLOR_CODE_UNKNOWN: ColorCode = 1;

pub trait ColorCodeExt {
    fn is_empty(self) -> bool;
    fn is_unknown(self) -> bool;
}

impl ColorCodeExt for ColorCode {
    fn is_empty(self) -> bool {
        self == COLOR_CODE_EMPTY
    }
    fn is_unknown(self) -> bool {
        self == COLOR_CODE_UNKNOWN
    }
}
