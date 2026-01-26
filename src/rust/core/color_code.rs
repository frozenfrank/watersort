use std::collections::HashMap;

use crate::core::{Color, color::{EMPTY_SPACE, UNKNOWN_VALUE}};

pub type ColorCode = u8;

pub struct ColorCodeAllocator<'a> {
	color_codes: HashMap<&'a Color<'a>, ColorCode>,
	colors: Vec<&'a Color<'a>>,
}

impl <'a> ColorCodeAllocator<'a> {
	pub fn new() -> Self {
		let mut allocator = Self {
            color_codes: HashMap::new(),
            colors: Vec::new(),
		};

        // Reserve 0 and 1 for EMPTY_SPACE and UNKNOWN_COLOR
        allocator.allocate_color(&Color(EMPTY_SPACE));
        allocator.allocate_color(&Color(UNKNOWN_VALUE));
        allocator
	}

    fn allocate_color(&mut self, color: &'a Color) -> ColorCode {
        let assigned_code = self.colors.len() as ColorCode;
        self.color_codes.insert(&color, assigned_code);
        self.colors.push(&color);
        assigned_code
    }

	pub fn assign_code(&mut self, color: &'a Color) -> ColorCode {
        // CONSIDER: Performing a linear search through self.colors while the array is small.
        // This could be cheaper since we expect the total number of colors to be normally small.
        if let Some(&code) = self.color_codes.get(&color) {
			code
		} else {
            self.allocate_color(color)
		}
	}

    pub fn interpret_code(&'a self, code: ColorCode) -> &'a Color<'a> {
        self.colors[code as usize]
    }
}
