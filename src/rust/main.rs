/// Main entry point for the Water Sort Puzzle CLI
use watersort::{
    Game,
    init::{Mode, choose_interaction},
    io::parser,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut game: Game;

    let interaction = choose_interaction();
    if interaction.mode == Mode::Quit {
        std::process::exit(0);
    }

    if interaction.mode != Mode::NewGame
        && let Some(level) = interaction.level
    {
        game = parser::read_game_level(&level)?;
    } else {
        // TODO: Attempt to read the game state out of a file
        unimplemented!("This version of watersort does not support reading in games manually.");
    }

    // TODO: Verify game is error-free
    // game.attempt_correct_errors()

    match interaction.mode {
        Mode::Play => watersort::play::play_game(&mut game),
        Mode::NewGame | Mode::Solve | Mode::Interact => {
            watersort::solver::solve_game(game.to_arc())
        }
        Mode::Analyze => unimplemented!("Analyze game functionality"),
        Mode::Quit => unreachable!("The program has already interpreted this option."),
        Mode::Unknown => {
            unreachable!("After selecting an interaction, game mode should always be known.")
        }
    }

    Ok(())
}
