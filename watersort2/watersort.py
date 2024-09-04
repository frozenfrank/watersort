from collections import deque, defaultdict
from math import floor, log
import random
from colorama import Fore, Back, Style
from time import time
import itertools

from constant import ENABLE_QUEUE_CHECKS, MIX_SWITCH_THRESHOLD_MOVES, RESERVED_COLORS, VALID_SOLVE_METHODS
from game import Game
from watersort2.menu import chooseInteraction

SOLVER_VERSION = 1
ANALYZER_VERSION = 5

def generateAnalysisResultsName(level: str, absolutePath = True) -> str:
  return getBasePath(absolutePath) + f"wsanalysis/{level}-{round(time())}.csv"
def saveAnalysisResults(rootGame: Game, seconds: float, samples: int,
                        partialStates, dupStates, deadStates, solStates, uniqueSolStates,
                        longestSolves, uniqueSolsDistribution, completionData: tuple[defaultdict[int, str], defaultdict[int, str]],
                        solveTimes: defaultdict[int] = None) -> None:
  # Generates a CSV file with data
  # This spreadsheet has been setup to analyze these data exports
  # https://docs.google.com/spreadsheets/d/1HK8ic2QTs1onlG_x7o9s0yXxY1Nl9mFLO9mHtou2RcA/edit#gid=1119310589

  extraDataLength = max(
    max(longestSolves.keys()),
    max(uniqueSolsDistribution.keys()))

  fileName = generateAnalysisResultsName(rootGame.level)
  headers = [
    ("Level", rootGame.level),
    ("Num Vials", rootGame.getNumVials()),
    ("Num colors", len(completionData[0])),
    # ("Secret", rootGame.secretMode), # TODO: Track this value to report here as well
    # ("Unique Solve Orders", len(uniqueSolutions)), # TODO: Get data in here!
    ("Seconds", round(seconds, 1)),
    ("Samples", samples),
    ("Solver Version", SOLVER_VERSION),
    ("Analyzer Version", ANALYZER_VERSION),
    ("Extra Data Length", extraDataLength),
  ]
  if solveTimes:
    headers.append(("Max Solution Seconds", max(solveTimes.keys())))

  columns = [
    ("Partial Game States", partialStates),
    ("Duplicate Game States", dupStates),
    ("Dead End States", deadStates),
    ("Solutions", solStates),
    ("Unique Solutions", uniqueSolStates),
    ("Longest Solves (s)", longestSolves),
    ("Unique Sol Distribution", uniqueSolsDistribution),
    ("Color Completion Data", completionData[0]),
    ("Depth Completion Data", completionData[1]),
  ]
  saveCSVFile(fileName, columns, headers, keyColumnName="Depth")
  print("Saved analysis results to file: " + fileName)
def printCounterDict(counter: defaultdict[int], title = "Counter:", indentation = "  ", keyWidth = 4) -> None:
  lines = []

  if title:
    lines.append(title)

  for key, count in sorted(counter.items()):
    lines.append(indentation + str(key).rjust(keyWidth) + ": " + str(count));

  print("\n".join(lines))
def identifyExtraDataLength(partialStatesDepthDict: defaultdict[int, int]) -> int:
  deepestGame = max(partialStatesDepthDict.keys()) + 1 # Because we add an empty row at the end of the CSV file
  return max(min(round(deepestGame // 5) * 5, 50), 1) # Round down to the nearest multiple of 5, capped at 50, minimum 5
def prepareLongestSolves(targetCount: int, solSolveTimes: defaultdict[float, int]) -> defaultdict[int, int]:
  longestSolvesList = list()
  for time, count in sorted(solSolveTimes.items(), reverse=True):
    longestSolvesList.extend(itertools.repeat(time, count))
    if len(longestSolvesList) >= targetCount:
      break

  longestSolvesDict = defaultdict(int)
  for i in range(min(targetCount, len(longestSolvesList))):
    longestSolvesDict[i + 1] = longestSolvesList[i]

  return longestSolvesDict
def prepareUniqueDistribution(targetCount: int, isUniqueList: list[bool]) -> defaultdict[int, int]:
  targetCount = min(targetCount, len(isUniqueList))
  divisor = len(isUniqueList) / targetCount

  uniqueSolvesDistribution = defaultdict(int)
  for index, isUnique in enumerate(isUniqueList):
    if isUnique:
      uniqueSolvesDistribution[int(1 + (index // divisor))] += 1

  return uniqueSolvesDistribution
def printUniqueSolutions(uniqueSolutions: defaultdict[int, list[Game]]) -> None:
  PRINT_SOL_COUNT = 15
  out = []

  out.append(f"Showing {PRINT_SOL_COUNT} of {len(uniqueSolutions)} unique completion orders\n  Occurrences \tOrder")
  for uniqueSolSet, index in zip(sorted(uniqueSolutions.values(), key= lambda x: len(x), reverse=True), range(PRINT_SOL_COUNT)):
    out.append(f"\n  {str(len(uniqueSolSet)).ljust(11)}")
    for color, depth in uniqueSolSet[0].completionOrder:
      out.append(f"\t{color} ({depth})")

  print("".join(out))
  pass
def prepareCompletionOrderData(rootGame: Game, uniqueSolutions: defaultdict[int, list[Game]]) -> tuple[defaultdict[int, str], defaultdict[int, str]]:
  # We're going to be creating ";" separate strings that occupy a single column,
  # but will be expanded into multiple columns for analysis
  # Remember that our output defaultdict's must be from range 1 to n

  # PREPARE ANALYSIS
  totalSamples = 0
  maxDepth = 0
  numColors, allColorsList = _initColors(rootGame)
  colorCompletionDict: defaultdict[str, tuple] = defaultdict(lambda: [0] * (numColors + 1))
  completionDepthDict: defaultdict[int, list[int]] = defaultdict(lambda: [0] * numColors)

  # COLOR COMPLETIONS
  # One row for each color
  # Each row has
  # - The color
  # - n entries indicating how many times that color appeared in the nth completion position

  # COMPLETION DEPTH
  # Up to one row for each solution depth
  # One column for each color
  # The number of times the nth color was completed at each depth (regardless of color)

  for solutionSet in uniqueSolutions.values():
    for solution in solutionSet:
      totalSamples += 1
      maxDepth = max(maxDepth, solution.getDepth())
      for index, (color, depth) in enumerate(solution.completionOrder):
        colorCompletionDict[color][index + 1] += 1
        completionDepthDict[depth][index] += 1

  # COMPILE DATA
  colorCompletions: defaultdict[int, str] = defaultdict(str)
  completionDepth: defaultdict[int, str] = defaultdict(str)

  # CONSIDER: Dividing all the numbers by a pre-calculated constant to that they are each less than 1000
  SEPARATOR = ";"
  for i, color in enumerate(allColorsList):
    colorCompletionDict[color][0] = color
    colorCompletions[i + 1] = SEPARATOR.join(map(str, colorCompletionDict[color]))
  for depth in range(1, maxDepth+1):
    completionDepth[depth] = SEPARATOR.join(map(str, completionDepthDict[depth]))

  # RETURN
  return (colorCompletions, completionDepth)
def _initColors(rootGame: Game) -> tuple[int, list[str]]: # (numColors, list_of_colors)
  colorOccurrences, _colorErrors = rootGame._analyzeColors()
  for reservedColor in RESERVED_COLORS:
    colorOccurrences[reservedColor] += 0
  # We know that ALL the reserved colors exist as keys in the dictionary
  numColors = len(colorOccurrences) - len(RESERVED_COLORS)

  allColorsList = []
  for color in sorted(colorOccurrences.keys()):
    if color in RESERVED_COLORS:
      continue
    allColorsList.append(color)

  return (numColors, allColorsList)
# Given an int with any number of digits (base 10),
# It will return at most the `digits` number of the highest order digits
def preserveHighestOrderDigits(x: int, digits=5) -> int:
  return x // (10 ** max(floor(log(x, 10) - digits + 1), 0))

def saveCSVFile(fileName: str, columns: list[tuple[str, defaultdict[int, any]]], headers: list[tuple[str, ...]] = None, keyColumnName = "Key") -> None:
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

# Run the program!
# Call signatures:
# py watersort.py LEVEL a SAMPLES?
# py watersort.py a LEVEL SAMPLES?
# py watersort.py LEVEL <MODE>
# py watersort.py LEVEL dfr SAMPLES?
chooseInteraction()
