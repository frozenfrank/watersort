use std::{collections::HashMap, rc::Rc};

use crate::core::{Color, color::{EMPTY_SPACE, UNKNOWN_VALUE}};

pub type ColorCode = u8;


pub trait ColorCodeExt {
    fn is_empty(self) -> bool;
    fn is_unknown(self) -> bool;
}

impl ColorCodeExt for ColorCode {
    fn is_empty(self) -> bool {
        self == 0
    }
    fn is_unknown(self) -> bool {
        self == 1
    }
}

pub struct ColorCodeAllocator {
	color_codes: HashMap<Rc<Color>, ColorCode>,
	colors: Vec<Rc<Color>>,
}

impl ColorCodeAllocator {
	pub fn new() -> Self {
		let mut allocator = Self {
            color_codes: HashMap::new(),
            colors: Vec::new(),
		};

        // Reserve 0 and 1 for EMPTY_SPACE and UNKNOWN_COLOR
        allocator.allocate_color(&Color::new(EMPTY_SPACE));
        allocator.allocate_color(&Color::new(UNKNOWN_VALUE));
        allocator
	}

    fn allocate_color(&mut self, color: &Color) -> ColorCode {
        let assigned_code = self.colors.len() as ColorCode;
        let boxed_color = Rc::new(color.clone());
        self.color_codes.insert(boxed_color.clone(), assigned_code);
        self.colors.push(boxed_color);
        assigned_code
    }

	pub fn assign_code(&mut self, color: &Color) -> ColorCode {
        // CONSIDER: Performing a linear search through self.colors while the array is small.
        // This could be cheaper since we expect the total number of colors to be normally small.
        if let Some(&code) = self.color_codes.get(color) {
			code
		} else {
            self.allocate_color(&color)
		}
	}

    pub fn interpret_code(&self, code: ColorCode) -> Rc<Color> {
        self.colors[code as usize].clone()
    }
}
