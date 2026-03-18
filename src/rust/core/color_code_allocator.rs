use crate::{
    core::{
        Color, ColorCode,
        color::{EMPTY_SPACE, UNKNOWN_VALUE},
    },
    display::colors::DEFAULT_COLORS,
};
use std::{cmp::max, collections::HashMap, rc::Rc};

#[derive(Clone, PartialEq, Eq)]
pub struct ColorCodeAllocator {
    color_codes: HashMap<Rc<Color>, ColorCode>,
    colors: Vec<Rc<Color>>,
    max_name_len: usize,
}

impl ColorCodeAllocator {
    // Allocates only the bare minimum colors for use
    pub fn new_bare() -> Self {
        let mut allocator = Self {
            color_codes: HashMap::new(),
            colors: Vec::new(),
            max_name_len: 0,
        };

        // Reserve 0 and 1 for EMPTY_SPACE and UNKNOWN_COLOR
        allocator.allocate_color(&Color::new(EMPTY_SPACE));
        allocator.allocate_color(&Color::new(UNKNOWN_VALUE));
        allocator
    }

    /// Allocates with all the default colors included
    pub fn new() -> Self {
        let mut allocator = ColorCodeAllocator::new_bare();

        for color in DEFAULT_COLORS.iter() {
            allocator.allocate_color(color);
        }

        allocator
    }

    fn allocate_color(&mut self, color: &Color) -> ColorCode {
        let assigned_code = self.colors.len() as ColorCode;
        let boxed_color = Rc::new(color.clone());
        self.color_codes.insert(boxed_color.clone(), assigned_code);
        self.colors.push(boxed_color);
        if let Some(color_name) = color.name {
            self.max_name_len = max(self.max_name_len, color_name.len());
        }
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

    pub fn interpret_code_as_ref(&self, code: ColorCode) -> &Color {
        &*self.colors[code as usize]
    }

    pub fn num_colors(&self) -> usize {
        self.colors.len() - 2 // Subtract 2 for EMPTY_SPACE and UNKNOWN_COLOR
    }

    pub fn max_color_name_len(&self) -> usize {
        self.max_name_len
    }
}

impl std::fmt::Debug for ColorCodeAllocator {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ColorCodeAllocator")
            // .field("color_codes", &self.color_codes)
            .field(
                "colors",
                &self
                    .colors
                    .iter()
                    .map(|color| &color.key)
                    .collect::<Vec<_>>(),
            )
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bare_creation_minimums() {
        let allocator = ColorCodeAllocator::new_bare();

        assert_eq!(allocator.interpret_code(0).key, EMPTY_SPACE);
        assert_eq!(allocator.interpret_code(1).key, UNKNOWN_VALUE);
    }

    #[test]
    fn test_default_creation_minimums() {
        let allocator = ColorCodeAllocator::new();

        assert_eq!(allocator.interpret_code(0).key, EMPTY_SPACE);
        assert_eq!(allocator.interpret_code(1).key, UNKNOWN_VALUE);
    }
}
