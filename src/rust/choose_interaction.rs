// choose_interaction.rs
// Ported from Python's chooseInteraction() logic in watersort.py
// This module provides a function to handle user interaction and mode selection for the game.

use std::collections::HashSet;
use std::env;
use std::io::{self, Write};

// Placeholder types and constants. Replace with actual implementations.
const ANALYZE_ATTEMPTS: usize = 100;
const DFR_SEARCH_ATTEMPTS: usize = 100;
const FORCE_SOLVE_LEVEL: Option<&str> = None;
const FORCE_INTERACTION_MODE: Option<&str> = None;
const SOLVE_METHOD: &str = "MIX";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Play,
    Solve,
    Interact,
    Analyze,
    Quit,
    Debug,
    Unknown,
}

impl Mode {
    fn from_str(s: &str) -> Option<Self> {
        match s {
            "p" => Some(Mode::Play),
            "s" => Some(Mode::Solve),
            "q" => Some(Mode::Quit),
            "i" => Some(Mode::Interact),
            "a" => Some(Mode::Analyze),
            "d" => Some(Mode::Debug),
            _ => None,
        }
    }
}

/// Represents the User's choice of intended utility behavior
pub struct InteractionResult {
    pub mode: Mode,
    pub level: Option<String>,
    pub drain_mode: bool,
    pub blind_mode: bool,
    pub analyze_samples: usize,
    pub dfr_search_attempts: usize,
}

pub fn choose_interaction() -> InteractionResult {
    let valid_modes: HashSet<&str> = ["p", "s", "q", "i", "n"].iter().cloned().collect();
    let mut mode: Option<Mode> = None;
    let mut level: Option<String> = None;
    let mut drain_mode = false;
    let mut blind_mode = false;
    let mut user_interacting = true;
    let mut analyze_samples = ANALYZE_ATTEMPTS;
    let mut dfr_search_attempts = DFR_SEARCH_ATTEMPTS;

    // Level override
    if let Some(force_level) = FORCE_SOLVE_LEVEL {
        level = Some(force_level.to_string());
        mode = Some(Mode::from_str(FORCE_INTERACTION_MODE.unwrap_or("i")).unwrap_or(Mode::Interact));
        println!("FORCING SOLVE LEVEL to {}. Mode={:?}", force_level, mode);
    } else {
        let args: Vec<String> = env::args().collect();
        if args.len() > 1 {
            if args[1] == "a" {
                mode = Some(Mode::Analyze);
                if args.len() > 2 {
                    level = Some(args[2].clone());
                }
                if args.len() > 3 {
                    analyze_samples = args[3].parse().unwrap_or(ANALYZE_ATTEMPTS);
                }
            } else {
                // Special modes
                let mut args = args;
                if let Some(pos) = args.iter().position(|x| x == "drain") {
                    drain_mode = true;
                    args.remove(pos);
                }
                if let Some(pos) = args.iter().position(|x| x == "blind") {
                    blind_mode = true;
                    args.remove(pos);
                }
                mode = Some(Mode::Interact);
                level = Some(args[1].clone());
                if args.len() > 2 {
                    if args[2] == "a" {
                        mode = Some(Mode::Analyze);
                        if args.len() > 3 {
                            analyze_samples = args[3].parse().unwrap_or(ANALYZE_ATTEMPTS);
                        }
                    } else {
                        // set_solve_method(args[2].as_str());
                    }
                }
                if args.len() > 3 && SOLVE_METHOD == "DFR" {
                    dfr_search_attempts = args[3].parse().unwrap_or(DFR_SEARCH_ATTEMPTS);
                }
            }
        }
    }

    // Request the mode if not set
    while mode.is_none() {
        println!(r#"
          How are we interacting?
          NAME                      level name
          p LEVEL?                  play
          n                         solve (from new input)
          i                         interact (or resume an existing game)
          a LEVEL? SAMPLES?         analyze
          q                         quit
          d                         debug mode
          m METHOD                  method of solving
          "#);
        print!("> ");
        io::stdout().flush().unwrap();
        let mut response = String::new();
        io::stdin().read_line(&mut response).unwrap();
        let response = response.trim();
        let words: Vec<&str> = response.split_whitespace().collect();
        let first_word = words.get(0).copied().unwrap_or("");
        match first_word {
            "d" => {
                // Toggle debug mode (implement as needed)
                // DEBUG_ONLY = !DEBUG_ONLY;
            }
            "m" => {
                if words.len() < 2 {
                    println!("Cannot set the solve method without the method as well");
                } else {
                    // set_solve_method(words[1]);
                }
            }
            "a" => {
                mode = Some(Mode::Analyze);
                if words.len() > 1 {
                    level = Some(words[1].to_string());
                }
                if words.len() > 2 {
                    analyze_samples = words[2].parse().unwrap_or(ANALYZE_ATTEMPTS);
                }
            }
            "p" => {
                mode = Some(Mode::Play);
                if words.len() > 1 {
                    level = Some(words[1].to_string());
                }
            }
            fw if valid_modes.contains(fw) => {
                mode = Mode::from_str(fw);
                if mode == Some(Mode::Interact) {
                    user_interacting = false;
                }
            }
            _ => {
                level = Some(response.to_string());
                mode = Some(Mode::Interact);
            }
        }
    }

    if mode == Some(Mode::Quit) {
        std::process::exit(0);
    }

    // Read initial state if needed
    if matches!(mode, Some(Mode::Interact) | Some(Mode::Solve) | Some(Mode::Analyze) | Some(Mode::Unknown)) && level.is_none() {
        if user_interacting {
            println!("What level is this?");
        }
        let mut input_level = String::new();
        io::stdin().read_line(&mut input_level).unwrap();
        level = Some(input_level.trim().to_string());
    }

    // The rest of the logic (file reading, game state, etc.) should be implemented as needed.
    // This function returns the parsed interaction result.
    InteractionResult {
        mode: mode.unwrap_or(Mode::Unknown),
        level,
        drain_mode,
        blind_mode,
        analyze_samples,
        dfr_search_attempts,
    }
}

// Add additional functions for play_game, solve_game, save_game, etc. as needed.
