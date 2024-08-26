
import sys
from watersort2.constant import ANALYZE_ATTEMPTS, DFR_SEARCH_ATTEMPTS, FORCE_INTERACTION_MODE, FORCE_SOLVE_LEVEL
from watersort2.game import Game
from watersort2.game_files import generateLevelFileName, readGameFromFile, readGameFromInput
from watersort2.game_player import GamePlayer


def chooseInteraction():
  validModes = set("psqin")
  mode: str = None
  level: str = None
  userInteracting = True
  originalGame: Game | None = None
  analyzeSamples = ANALYZE_ATTEMPTS
  dfrSearchAttempts = DFR_SEARCH_ATTEMPTS

  # Allow different forms of level override
  if FORCE_SOLVE_LEVEL:
    # DEBUG
    level = FORCE_SOLVE_LEVEL
    mode = FORCE_INTERACTION_MODE or "i"
    print(f"FORCING SOLVE LEVEL to {level}. Mode={mode}")
  elif len(sys.argv) > 1:
    # COMMAND LINE

    # Analyze mode
    if sys.argv[1] == "a":
      mode = "a"
      if len(sys.argv) > 2:
        level = sys.argv[2]
      if len(sys.argv) > 3:
        analyzeSamples = int(sys.argv[3])

    # Playing a level
    else:
      mode = "i"
      level = sys.argv[1]

      # Read solve method
      if len(sys.argv) > 2:
        if sys.argv[2] == "a":
          mode = "a"
          if len(sys.argv) > 3:
            analyzeSamples = int(sys.argv[3])
        else:
          setSolveMethod(sys.argv[2])
      if len(sys.argv) > 3 and SOLVE_METHOD == "DFR":
        dfrSearchAttempts = int(sys.argv[3])


  # Request the mode
  while not mode:
    print("""
          How are we interacting?
          NAME                      level name
          p                         play
          n                         solve (from new input)
          i                         interact (or resume an existing game)
          a LEVEL? SAMPLES?         analyze
          q                         quit
          d                         debug mode
          m METHOD                  method of solving
          """)
    response = input().strip()
    words = response.split()
    firstWord = words[0]
    if firstWord == "d":
      global DEBUG_ONLY
      DEBUG_ONLY = not DEBUG_ONLY
    elif firstWord == "m":
      if len(words) < 2:
        print("Cannot set the solve method without the method as well")
      else:
        setSolveMethod(words[1])
    elif firstWord == "a":
      mode = "a"
      if len(words) > 1:
        level = words[1]
      if len(words) > 2:
        analyzeSamples = int(words[2])
    elif firstWord in validModes:
      mode = firstWord
      if mode == "i":
        userInteracting = False
    else:
      level = response
      mode = "i"

  if mode == "q":
    quit()

  # Read initial state
  if (mode == "i" or mode == "s" or mode == "a" or mode == "n") and not level:
    if userInteracting:
      print("What level is this?")
    level = input()

  # Attempt to read the game state out of a file
  if mode != "n" and level:
    gameFileName = generateLevelFileName(level)
    originalGame = readGameFromFile(gameFileName, level)

  if originalGame and level:
    originalGame.level = level


  # Fallback to reading in manually
  if not originalGame:
    originalGame = readGameFromInput(userInteracting)
    if level != None:
      originalGame.level = level
    saveGame(originalGame)

  # Verify game has no error
  if originalGame.attemptCorrectErrors():
    print("Attempts to resolve the errors did not work. Abandoning program.")
    return

  # Choose mode
  if mode == "p":
    GamePlayer.Play(originalGame)
  elif mode == "i" or mode == "s" or mode == "n":
    solveGame(originalGame, solveMethod=SOLVE_METHOD, probeDFRSamples=dfrSearchAttempts)
    saveGame(originalGame)
  elif mode == "a":
    global SHUFFLE_NEXT_MOVES
    SHUFFLE_NEXT_MOVES = True
    solveGame(originalGame, solveMethod="DFS", analyzeSampleCount=analyzeSamples)
  else:
    print("Unrecognized mode: " + mode)

  quit(0)