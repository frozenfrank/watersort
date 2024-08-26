
from typing import Callable
from watersort2.game import NUM_SPACES_PER_VIAL, Game

# Read game methods
def readGameFromInput(userInteracting: bool) -> Game:
  game = _readGame(input, userInteraction=userInteracting)
  game.modified = True
  return game
def readGameFromFile(gameFileName: str, level: str = None) -> Game | None:
  gameRead: Game = None
  try:
    gameFile = open(gameFileName, "r")
    nextLine = lambda: gameFile.readline().strip()

    mode = nextLine()               # Read mode
    if mode == "i":
      level = nextLine()            # Read level name
    gameRead = _readGame(nextLine)
    gameRead.level = level

    gameFile.close()
  except FileNotFoundError:
    print("Attempted to resume progress, but no file exists for this level.")
    # The file doesn't exist, just ask for it from the user
  else:
    print("Resumed game progress from saved file " + gameFileName)
  finally:
    return gameRead
def _readGame(nextLine: Callable[[], str], userInteraction = False) -> Game:
  if userInteraction: print("How many vials are in this game?")
  numVials = None
  while not numVials:
    rsp = nextLine()  # Read num vials
    if rsp.isnumeric():
      numVials = int(rsp)
    elif rsp == "quit" or rsp == "q" or rsp == "-q":
      quit()
    else:
      print("We asked for the number of vials. That's not a number.")

  vials = []

  # Automatically detect the last empty vials
  numEmpty = 0
  if userInteraction:
    numEmpty = 2
    if numVials < 7: # I actually don't know if this is the threshold. There may other thresholds at higher counts
      numEmpty = 1

  # Read in the colors
  if userInteraction: print(f"On the next {numVials} lines, please type {NUM_SPACES_PER_VIAL} words representing the colors in each vial from top to bottom.\n"+
                            "  Stopping short of the depth of a vial will fill the remaining spaces with question marks.\n" +
                            "  Type a . (period) to insert a whole row of question marks.\n" +
                            "  Type a blank line to mark the remaining vials as empty.\n")
  emptyRest = False
  i = 0
  while i < numVials:
    i += 1
    if emptyRest or i > numVials - numEmpty:
      vials.append(["-"] * NUM_SPACES_PER_VIAL)
      continue

    if userInteraction: print(f"Vial {i}: ")
    response = nextLine()
    if response == "" or not response:
      emptyRest = True
      i -= 1 # Place an empty value for this row
      continue

    if response == ".":
      vials.append(["?"] * NUM_SPACES_PER_VIAL)
      continue

    spaces = response.split()
    while len(spaces) < NUM_SPACES_PER_VIAL:
      spaces.append("?")
    vials.append(spaces)

  return Game.Create(vials)

# Save game methods
def saveGame(game: "Game", forceSave = False) -> None:
  if not forceSave and not game.modified:
    return None # No saving necessary
  fileName = generateLevelFileName(game.level)
  result = generateFileContents(game)
  saveFileContents(fileName, result)
  game.modified = False
  print(f"Saved discovered game state to file: {fileName}")
def getBasePath(absolutePath = True) -> str:
  return "/Users/frozenfrank/Documents/College/Fall 2023/CPC/personal/" if absolutePath else ""
def generateLevelFileName(levelNum: str, absolutePath = True) -> str:
  return getBasePath(absolutePath) + f"wslevels/{levelNum}.txt"
def generateFileContents(game: "Game") -> str:
  lines = list()
  lines.append("i")
  lines.append(str(game.level))
  lines.append(str(len(game.vials)))
  for vial in game.vials:
    lines.append("\t".join(vial))
  # lines.append("")
  return "\n".join(lines)
def saveFileContents(fileName: str, contents: str) -> None:
  sourceFile = open(fileName, 'w')
  print(contents, file = sourceFile)
  sourceFile.close()
