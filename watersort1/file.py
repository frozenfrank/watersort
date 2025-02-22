from collections import defaultdict
from personal.watersort.game import Game

BASE_PATH = "/Users/frozenfrank/Documents/College/Fall 2023/CPC/personal/watersort/"
LEVEL_FOLDER_NAME = "wslevels/"

def saveGame(game: Game, forceSave = False) -> None:
  if not forceSave and not game.modified:
    return # No saving necessary
  if not game.level:
    print("Cannot save the game without the level defined.")
    return # Cannot save without a level

  fileName = _generateFileName(game.level)
  result = _generateFileContents(game)
  _saveFileContents(fileName, result)
  game.modified = False
  print(f"Saved discovered game state to file: {fileName}")
def saveCSVFile(fileName: str, columns: list[tuple[str, defaultdict]], headers: list[tuple[str, ...]] = None, keyColumnName = "Key") -> None:
  # Creates a CSV file with the following format:
  # The first several data rows contain special STRING-VALUE pairs of special data (headers)

  # Key, Col Name 1, Col Name 2...
  # Level, LEVEL
  # Seconds, SECONDS
  # Samples, SAMPLES
  # 1, val 1, val 2...
  # 2, val 1, val 2...
  # 3, val 1, val 2...

  lines = []
  row = []
  maxIndex = float("-inf")
  minIndex = float("inf")

  # Process columns into header row
  row.append(keyColumnName)
  for colName, dictValues in columns:
    row.append(colName)
    maxIndex = max(maxIndex, *dictValues.keys())
    minIndex = min(minIndex, *dictValues.keys())
  lines.append(",".join(row))

  # Insert special rows of headers
  if headers:
    for header in headers:
      lines.append(",".join(map(str, header)))

  # Add all data in the dicts
  for i in range(minIndex, maxIndex + 1):
    row.clear()
    row.append(i)
    for colName, dictValues in columns:
      row.append(dictValues[i])
    lines.append(",".join(map(str, row)))

  # Add a row of zeros
  row = [0] * (1 + len(columns))
  row[0] = maxIndex + 1
  lines.append(",".join(map(str, row)))

  # End with newline
  lines.append("")

  # Finish
  saveFileContents(fileName, "\n".join(lines))
def _saveFileContents(fileName: str, contents: str) -> None:
  sourceFile = open(fileName, 'w')
  print(contents, file = sourceFile)
  sourceFile.close()

def _getBasePath(absolutePath = True) -> str:
  return BASE_PATH if absolutePath else ""
def _generateFileName(levelNum: str, absolutePath = True) -> str:
  return _getBasePath(absolutePath) + LEVEL_FOLDER_NAME + f"{levelNum}.txt"
def _generateFileContents(game: Game) -> str:
  lines = list()
  lines.append("i")
  lines.append(str(game.level))
  lines.append(str(len(game.vials)))
  for vial in game.vials:
    lines.append("\t".join(vial))
  # lines.append("")
  return "\n".join(lines)
