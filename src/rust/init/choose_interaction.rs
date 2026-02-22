// choose_interaction.rs
// Ported from Python's chooseInteraction() logic in watersort.py
// This module provides a function to handle user interaction and mode selection for the game.

use std::env;
use std::io::{self, Write};

use crate::init::Mode;
use crate::init::interaction_result::InteractionResult;
use crate::utils::helpers::vec_take;
use crate::{
    DEFAULT_ANALYZE_ATTEMPTS, DEFAULT_DFR_SEARCH_ATTEMPTS, FORCE_INTERACTION_MODE,
    FORCE_SOLVE_LEVEL,
};

pub fn choose_interaction() -> InteractionResult {
    let mut result = InteractionResult::default();

    if let Some(force_level) = FORCE_SOLVE_LEVEL {
        result.level = Some(force_level.to_string());
        result.mode = FORCE_INTERACTION_MODE.unwrap_or(Mode::Interact);
        println!(
            "FORCING SOLVE LEVEL to {}. Mode={:?}",
            force_level, result.mode
        );
    } else {
        interpret_command_args(&mut result);
    }

    if result.mode == Mode::Unknown {
        prompt_for_mode(&mut result);
    }

    assert_ne!(
        result.mode,
        Mode::Unknown,
        "Mode is known after prompting user"
    );

    // Step 4: Handle quit
    if result.mode == Mode::Quit {
        return result;
    }

    // Step 5: Prompt for level if needed
    if matches!(
        result.mode,
        Mode::Interact | Mode::Solve | Mode::Analyze | Mode::NewGame
    ) && result.level.is_none()
    {
        if result.user_interacting {
            result.level = prompt_for_level();
        }
    }

    result
}

fn interpret_command_args(result: &mut InteractionResult) {
    let mut args: Vec<String> = env::args().collect();
    if args.len() <= 1 {
        return;
    }

    // Analyze Mode
    if args[1] == "a" {
        let analyze_samples = args.get(3).map(|s| s.as_str());
        result.set_analyze_mode(analyze_samples);
        if args.len() > 2 {
            result.level = Some(vec_take(&mut args, 2));
        }

    // Discover and solve a level
    } else {
        // Determine special modes
        if let Some(pos) = args.iter().position(|x| x == "drain") {
            result.known_drain_mode = Some(true);
            args.remove(pos);
        }
        if let Some(pos) = args.iter().position(|x| x == "blind") {
            result.known_blind_mode = Some(true);
            args.remove(pos);
        }

        result.mode = Mode::Interact;
        result.level = Some(args[1].clone());

        // Read solve method
        if args.len() > 2 {
            if args[2] == "a" {
                let analyze_samples = args.get(3).map(|s| s.as_str());
                result.set_analyze_mode(analyze_samples);
            } else {
                result.solve_method = Some(args[2].to_string());
            }
        }

        // Read DFR search attempts
        if result.solve_method.as_deref() == Some("DFR") {
            result.num_iterations = DEFAULT_DFR_SEARCH_ATTEMPTS;
            if args.len() > 3
                && let Ok(dfr_search_attempts) = args[3].parse()
            {
                result.num_iterations = dfr_search_attempts;
            }
        }
    }
}

// Prompt the user for mode and related info if not set by args
fn prompt_for_mode(result: &mut InteractionResult) {
    let mut response = String::new();

    while result.mode == Mode::Unknown {
        #[rustfmt::skip]
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
        // first_word.make_ascii_lowercase();

        match first_word {
            "d" => {
                println!("{:?}", response);
            }
            "m" => {
                if words.len() < 2 {
                    println!("Cannot set the solve method without the method as well");
                } else {
                    result.solve_method = Some(words[1].to_string());
                }
            }
            "a" => {
                result.set_analyze_mode(words.get(2).map(|w| &**w));
                if words.len() > 1 {
                    result.level = Some(words[1].to_string());
                }
            }
            "p" => {
                result.mode = Mode::Play;
                if words.len() > 1 {
                    result.level = Some(words[1].to_string());
                }
            }
            _ => {
                let mode = Mode::from_str(first_word);
                if mode != Mode::Unknown {
                    result.mode = mode;
                    if result.mode == Mode::Interact {
                        result.user_interacting = false;
                    }
                } else {
                    result.level = Some(response.to_string());
                    result.mode = Mode::Interact;
                }
            }
        }
    }
}

// Prompt the user for the level name if needed
fn prompt_for_level() -> Option<String> {
    println!("What level is this?");
    let mut input_level = String::new();
    io::stdin().read_line(&mut input_level).unwrap();
    Some(input_level.trim().to_string())
}

impl InteractionResult {
    pub fn set_analyze_mode(&mut self, analyze_samples: Option<&str>) {
        self.mode = Mode::Analyze;
        self.num_iterations = DEFAULT_ANALYZE_ATTEMPTS;
        if let Some(samples) = analyze_samples
            && let Ok(analyze_samples) = samples.parse()
        {
            self.num_iterations = analyze_samples;
        }
    }
}
