// choose_interaction.rs
// Ported from Python's chooseInteraction() logic in watersort.py
// This module provides a function to handle user interaction and mode selection for the game.

use std::collections::HashSet;
use std::env;
use std::io::{self, Write};

use crate::{DEFAULT_ANALYZE_ATTEMPTS, DEFAULT_DFR_SEARCH_ATTEMPTS, DEFAULT_SOLVE_METHOD, FORCE_INTERACTION_MODE, FORCE_SOLVE_LEVEL};


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

impl Default for Mode {
    fn default() -> Self {
        Mode::Unknown
    }
}

/// Represents the User's choice of intended utility behavior
#[derive(Default)]
pub struct InteractionResult {
    pub mode: Mode,
    pub level: Option<String>,
    pub known_drain_mode: Option<bool>,
    pub known_blind_mode: Option<bool>,
    /// If the mode supports repeating actions, this is the number of times to repeat the action.
    pub num_iterations: usize,
}


pub fn choose_interaction() -> InteractionResult {
    // Step 1: Check for forced level/mode
    if let Some(force_level) = FORCE_SOLVE_LEVEL {
        let mode = Mode::from_str(FORCE_INTERACTION_MODE.unwrap_or("i")).unwrap_or(Mode::Interact);
        println!("FORCING SOLVE LEVEL to {}. Mode={:?}", force_level, mode);
        return InteractionResult {
            mode,
            level: Some(force_level.to_string()),
            known_drain_mode: None,
            known_blind_mode: None,
            num_iterations: DEFAULT_ANALYZE_ATTEMPTS,
        };
    }

    // Step 2: Parse command-line arguments
    let (mut mode, mut level, drain_mode, blind_mode, mut analyze_samples, dfr_search_attempts) =
        parse_args();

    // Step 3: Prompt for mode if not set
    let mut user_interacting = true;
    if mode.is_none() {
        let prompt_result = prompt_for_mode();
        mode = prompt_result.0;
        level = prompt_result.1;
        analyze_samples = prompt_result.2;
        user_interacting = prompt_result.3;
    }

    // Step 4: Handle quit
    if mode == Some(Mode::Quit) {
        std::process::exit(0);
    }

    // Step 5: Prompt for level if needed
    if matches!(mode, Some(Mode::Interact) | Some(Mode::Solve) | Some(Mode::Analyze) | Some(Mode::Unknown)) && level.is_none() {
        if user_interacting {
            level = prompt_for_level();
        }
    }

    InteractionResult {
        mode: mode.unwrap_or(Mode::Unknown),
        level,
        known_drain_mode: Some(drain_mode),
        known_blind_mode: Some(blind_mode),
        num_iterations: analyze_samples,
    }
}

// Parse command-line arguments for mode, level, and flags
fn parse_args() -> (Option<Mode>, Option<String>, bool, bool, usize, usize) {
    let mut mode: Option<Mode> = None;
    let mut level: Option<String> = None;
    let mut drain_mode = false;
    let mut blind_mode = false;
    let mut analyze_samples = DEFAULT_ANALYZE_ATTEMPTS;
    let mut dfr_search_attempts = DEFAULT_DFR_SEARCH_ATTEMPTS;
    let args: Vec<String> = env::args().collect();
    if args.len() > 1 {
        if args[1] == "a" {
            mode = Some(Mode::Analyze);
            if args.len() > 2 {
                level = Some(args[2].clone());
            }
            if args.len() > 3 {
                analyze_samples = args[3].parse().unwrap_or(DEFAULT_ANALYZE_ATTEMPTS);
            }
        } else {
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
                        analyze_samples = args[3].parse().unwrap_or(DEFAULT_ANALYZE_ATTEMPTS);
                    }
                } else {
                    // set_solve_method(args[2].as_str());
                }
            }
            if args.len() > 3 && DEFAULT_SOLVE_METHOD == "DFR" {
                dfr_search_attempts = args[3].parse().unwrap_or(DEFAULT_DFR_SEARCH_ATTEMPTS);
            }
        }
    }
    (mode, level, drain_mode, blind_mode, analyze_samples, dfr_search_attempts)
}

// Prompt the user for mode and related info if not set by args
fn prompt_for_mode() -> (Option<Mode>, Option<String>, usize, bool) {
    let valid_modes = valid_modes();
    let mut mode: Option<Mode> = None;
    let mut level: Option<String> = None;
    let mut analyze_samples = DEFAULT_ANALYZE_ATTEMPTS;
    let mut user_interacting = true;

    let mut response = String::new();

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
        response.clear();
        io::stdin().read_line(&mut response).unwrap();
        let response = response.trim();
        let words: Vec<&str> = response.split_whitespace().collect();
        let first_word = words.get(0).copied().unwrap_or("");
        match first_word {
            "d" => {
                // Toggle debug mode (implement as needed)
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
                    analyze_samples = words[2].parse().unwrap_or(DEFAULT_ANALYZE_ATTEMPTS);
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
    (mode, level, analyze_samples, user_interacting)
}

// Prompt the user for the level name if needed
fn prompt_for_level() -> Option<String> {
    println!("What level is this?");
    let mut input_level = String::new();
    io::stdin().read_line(&mut input_level).unwrap();
    Some(input_level.trim().to_string())
}


fn valid_modes() -> HashSet<&'static str> {
    ["p", "s", "q", "i", "n"].iter().cloned().collect()
}
