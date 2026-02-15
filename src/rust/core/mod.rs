/// Core module exports

pub mod game;
pub mod game_settings;
pub mod color;
pub mod color_code;
pub mod color_code_demo;

pub use game::Game;
pub use color::Color;
pub use color_code::{ColorCode, ColorCodeAllocator, ColorCodeExt};
pub use color_code_demo::run_color_allocator_debug;
