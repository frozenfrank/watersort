from collections import defaultdict
from time import time
from personal.watersort.file import _getBasePath
from personal.watersort.game import Game
from personal.watersort.snippet import analyzeCounterDictionary, fPercent, getTimeRunning, printCounterDict
from personal.watersort.solver_base import Solver


class AnalyzerSolver(Solver):

  REPORT_SEC_FREQ = 15
  lastReportTime: int

  def __init__(self) -> None:
    super().__init__()

  # Override several solutions hooks
  def onStartSolve(self, game: Game) -> None:
    self.lastReportTime = 0
    return super().onStartSolve(game)
  def onNewSolution(self, solutionsRemaining: int):
    sv, st = self.getStats()
    timeCheck = time()

    if solutionsRemaining % 1000 == 0 or timeCheck - lastReportTime > self.REPORT_SEC_FREQ:
      print(f"Searching for {solutionsRemaining} more solutions. Running for {round(timeCheck - sv.startTime, 1)} seconds.")
      lastReportTime = timeCheck
  def onEndSolve(self) -> None:
    self._printAnalysisStats()
    self._saveResults()
  def _printAnalysisStats(self) -> None:
    sv, st = self.getStats()

    analyzeSampleCount = len(sv.allSolutions)
    secsAnalyzing, minsAnalyzing = getTimeRunning(sv.startTime, sv.endTime)

    # Print out interesting information to the console only
    minSolutionMoves, maxSolutionMoves, modeSolutionMoves, countUniqueSols = analyzeCounterDictionary(uniqueSolsDepth)
    minDeadEnd, lastDeadEnd, modeDeadEnds, _ = analyzeCounterDictionary(deadEndDepth)
    nDupSols = analyzeSampleCount - countUniqueSols
    minFindTime, maxFindTime, modeFindTime, _ = analyzeCounterDictionary(solFindSeconds);

    printCounterDict(solFindSeconds, title="Time to find Solutions:")

    print(f"""
        Finished analyzing solution space:
          * Note: These values are counted an independent occurrences. It's possible that
            the same states from multiple distinct samples found the same sets of game states.

          Report:
          {analyzeSampleCount           }\t   Analysis samples
          {secsAnalyzing                }\t   Seconds analyzing
          {minsAnalyzing                }\t   Minutes analyzing
          {maxFindTime                  }\t   Maximum solution find time
          {minDeadEnd                   }\t   Dead end (First)
          {modeDeadEnds                 }\t   Dead end (Mode)
          {lastDeadEnd                  }\t   Dead end (Last)
          {minSolutionMoves             }\t   Solution moves (Min)
          {modeSolutionMoves            }\t   Solution moves (Mode)
          {maxSolutionMoves             }\t   Solution moves (Max)
          {countUniqueSols              }\t   Unique solutions
          {fPercent(nDupSols, analyzeSampleCount)}\t   Percent duplicated solutions
          """)
  def _saveResults(self) -> None:
    sv, st = self.getStats()

    # Identify and prepare some extra data
    extraDataLen = identifyExtraDataLength(partialDepth)
    longestSolvesDict = prepareLongestSolves(extraDataLen, solFindSeconds)
    uniqueDistributionDict = prepareUniqueDistribution(extraDataLen, isUniqueList)

    saveAnalysisResults(\
      sv.root.level, sv.endTime - sv.startTime, analyzeSampleCount, \
      partialDepth, dupGameDepth, deadEndDepth, solutionDepth, uniqueSolsDepth, \
      longestSolvesDict, uniqueDistributionDict, solFindSeconds)

  def onNextIteration(self, current: Game, numIterations: int) -> None:
    '''Skip the standard checks that occur on each iteration'''
    pass


def generateAnalysisResultsName(level: str, absolutePath = True) -> str:
  return _getBasePath(absolutePath) + f"wsanalysis/{level}-{round(time())}.csv"
def saveAnalysisResults(level, seconds, samples, partialStates, dupStates, deadStates, solStates, uniqueSolStates, longestSolves, uniqueSolsDistribution, solveTimes: defaultdict[int] = None) -> None:
  # Generates a CSV file with data
  # This spreadsheet has been setup to analyze these data exports
  # https://docs.google.com/spreadsheets/d/1HK8ic2QTs1onlG_x7o9s0yXxY1Nl9mFLO9mHtou2RcA/edit#gid=1119310589

  extraDataLength = max(
    max(longestSolves.keys()),
    max(uniqueSolsDistribution.keys()))

  fileName = generateAnalysisResultsName(level)
  headers = [
    ("Level", level),
    ("Seconds", round(seconds, 1)),
    ("Samples", samples),
    ("Solver Version", SOLVER_VERSION),
    ("Analyzer Version", ANALYZER_VERSION),
    ("Extra Data Length", extraDataLength)
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
  return min(round(deepestGame // 5) * 5, 50) # Round down to the nearest multiple of 5, capped at 50
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
