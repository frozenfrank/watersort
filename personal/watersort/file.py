from personal.watersort.game import Game

BASE_PATH = "/Users/frozenfrank/Documents/College/Fall 2023/CPC/personal/watersort/"
LEVEL_FOLDER_NAME = "wslevels/"

def saveGame(game: "Game", forceSave = False) -> None:
  if not forceSave and not game.modified:
    return None # No saving necessary
  fileName = _generateFileName(game.level)
  result = _generateFileContents(game)
  _saveFileContents(fileName, result)
  game.modified = False
  print(f"Saved discovered game state to file: {fileName}")

def _getBasePath(absolutePath = True) -> str:
  return BASE_PATH if absolutePath else ""
def _generateFileName(levelNum: str, absolutePath = True) -> str:
  return _getBasePath(absolutePath) + LEVEL_FOLDER_NAME + f"{levelNum}.txt"
def _generateFileContents(game: "Game") -> str:
  lines = list()
  lines.append("i")
  lines.append(str(game.level))
  lines.append(str(len(game.vials)))
  for vial in game.vials:
    lines.append("\t".join(vial))
  # lines.append("")
  return "\n".join(lines)
def _saveFileContents(fileName: str, contents: str) -> None:
  sourceFile = open(fileName, 'w')
  print(contents, file = sourceFile)
  sourceFile.close()
