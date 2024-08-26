from collections import deque, defaultdict
from math import floor, log
import random
from colorama import Fore, Back, Style
from time import time
from typing import Callable
import itertools
import sys

from constant import ANALYZE_ATTEMPTS, ENABLE_QUEUE_CHECKS, FORCE_INTERACTION_MODE, FORCE_SOLVE_LEVEL, MIX_SWITCH_THRESHOLD_MOVES, RESERVED_COLORS, VALID_SOLVE_METHODS
from files import generateFileName, getBasePath, saveFileContents, saveGame
from game import NUM_SPACES_PER_VIAL, Game
from watersort2.game_player import GamePlayer

SOLVER_VERSION = 1
ANALYZER_VERSION = 5

def solveGame(game: "Game", solveMethod = "MIX", analyzeSampleCount = 0, probeDFRSamples = 0):
  # Intelligent search through all the possible game states until we find a solution.
  # The game already handles asking for more information as required
  setSolveMethod(solveMethod)

  minSolution: Game = None
  numResets = -1
  randomSamplesRemaining = probeDFRSamples if solveMethod == "DFR" else 0

  startTime: float = None
  endTime: float = None

  minSolutionUpdates = 0
  numSolutionsAbandoned = 0


  # Analyzing variables
  analysisStart: float = time()
  REPORT_ITERATION_FREQ = 10000 if solveMethod == "BFS" else 1000
  QUEUE_CHECK_FREQ = REPORT_ITERATION_FREQ * 10
  partialDepth = defaultdict(int)
  dupGameDepth = defaultdict(int)
  deadEndDepth = defaultdict(int)
  solutionDepth = defaultdict(int)
  uniqueSolsDepth = defaultdict(int)
  solFindSeconds = defaultdict(int)
  uniqueSolutions: defaultdict[int, list["Game"]] = defaultdict(list)
  isUniqueList: list[bool] = list()

  deadEndDepth[1]
  analysisSamplesRemaining = analyzeSampleCount
  lastReportTime = 0
  REPORT_SEC_FREQ = 15

  # Temp only
  timeCheck: float

  while Game.reset or not minSolution or randomSamplesRemaining > 0 or analysisSamplesRemaining > 0:
    Game.reset = False
    numResets += 1
    if randomSamplesRemaining > 0:
      randomSamplesRemaining -= 1
    elif analysisSamplesRemaining > 0:
      timeCheck = time()
      if analysisSamplesRemaining % 1000 == 0 or timeCheck - lastReportTime > REPORT_SEC_FREQ:
        print(f"Searching for {analysisSamplesRemaining} more solutions. Running for {round(timeCheck - analysisStart, 1)} seconds. ")
        lastReportTime = timeCheck
      analysisSamplesRemaining -= 1


    # First correct any errors in the game
    game.attemptCorrectErrors()

    startTime = time()

    # Setup our search
    solution: Game | None = None
    q: deque["Game"] = deque()
    computed: set["Game"] = set()
    q.append(game)
    searchBFS: bool = shouldSearchBFS()

    numIterations = 0
    numDeadEnds = 0
    numPartialSolutionsGenerated = 0
    numDuplicateGames = 0
    maxQueueLength = 1

    # CONSIDER: Switching our approach based on the state of the game
    # When we still have unknowns, we should find the shortest path to find an unknown,
    # and continue in that same path until we reach a dead end.
    # This makes it easier for a human to follow along in the game

    # Perform the search
    while q and not solution:
      # Break out
      if Game.reset or Game.quit:
        break

      # Taking from the front or the back makes all the difference between BFS and DFS
      current = q.popleft() if searchBFS else q.pop()

      # Perform some work at some checkpoints
      numIterations += 1
      if numIterations % REPORT_ITERATION_FREQ == 0 and not analyzeSampleCount:
        if solveMethod != "BFS":
          print(f"Checked {numIterations} iterations.")

        if solveMethod == "MIX" and searchBFS and current._numMoves >= MIX_SWITCH_THRESHOLD_MOVES:
          searchBFS = False
          print("Switching to DFS search for MIX solve method")
        elif numIterations % QUEUE_CHECK_FREQ == 0:
          if ENABLE_QUEUE_CHECKS and not searchBFS:
            current.requestVal(current, "This is a lot. Are you sure?", printState=False)
          else:
            print(f"QUEUE CHECK: \tresets: {numResets} \titrs: {numIterations} \tmvs: {current._numMoves} \tq len: {len(q)} \tends: {numDeadEnds} \tdup games: {numDuplicateGames} \tmins: {round((time() - startTime) / 60, 1)}")
            if solveMethod == "MIX":
              rsp = current.requestVal(current, "This is a lot. Would you like to switch to a faster approach? (Yes/no)", printState=False)
              rsp.lower()
              if rsp and rsp[0] == "y":
                searchBFS = False
                solveMethod = "DFS"
              else:
                pass

      # Prune if we've found a cheaper solution
      if solveMethod == "DFR" and minSolution and minSolution._numMoves <= current._numMoves:
        numSolutionsAbandoned += 1
        break # Quit this attempt, and try a different one

      # Check all next moves
      hasNextGame = False
      nextGames = current.generateNextGames()
      if SHUFFLE_NEXT_MOVES: random.shuffle(nextGames)
      for nextGame in nextGames:
        numPartialSolutionsGenerated += 1
        partialDepth[nextGame._numMoves] += 1

        if nextGame in computed:
          numDuplicateGames += 1
          dupGameDepth[nextGame._numMoves] += 1
          continue
        computed.add(nextGame)

        hasNextGame = True
        if nextGame.isFinished():
          solution = nextGame
          if not minSolution or solution._numMoves < minSolution._numMoves:
            minSolution = solution
            minSolutionUpdates += 1
          solutionDepth[solution._numMoves] += 1
          timeCheck = time()
          solFindSeconds[int((timeCheck - startTime + 0.9) // 1)] += 1

          solutionHash = solution._completion_hash()
          hashingList = uniqueSolutions[solutionHash]
          if not len(hashingList):
            uniqueSolsDepth[solution._numMoves] += 1
            isUniqueList.append(True)
          else:
            isUniqueList.append(False)
          hashingList.append(solution)
          break # Finish searching
        else:
          q.append(nextGame)

      # Maintain stats
      maxQueueLength = max(maxQueueLength, len(q))
      if not hasNextGame:
        numDeadEnds += 1
        deadEndDepth[current._numMoves] += 1

  # End timer
  endTime = time()

  # Print results
  if analyzeSampleCount > 0:
    secsAnalyzing, minsAnalyzing = getTimeRunning(analysisStart, endTime)

    # Print out interesting information to the console only
    print("")
    minSolutionMoves, maxSolutionMoves, modeSolutionMoves, countUniqueSols = analyzeCounterDictionary(uniqueSolsDepth)
    minDeadEnd, lastDeadEnd, modeDeadEnds, _ = analyzeCounterDictionary(deadEndDepth)
    nDupSols = analyzeSampleCount - countUniqueSols
    minFindTime, maxFindTime, modeFindTime, _ = analyzeCounterDictionary(solFindSeconds)

    # printUniqueSolutions(uniqueSolutions)

    printCounterDict(solFindSeconds, title="Time to find Solutions:")

    print(f"""
        Finished analyzing solution space:
          * Note: These values are counted as independent occurrences. It's possible that
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

    # Identify and prepare some extra data
    extraDataLen = identifyExtraDataLength(partialDepth)
    longestSolvesDict = prepareLongestSolves(extraDataLen, solFindSeconds)
    uniqueDistributionDict = prepareUniqueDistribution(extraDataLen, isUniqueList)
    completionData = prepareCompletionOrderData(game, uniqueSolutions)

    saveAnalysisResults(\
      game, endTime - analysisStart, analyzeSampleCount, \
      partialDepth, dupGameDepth, deadEndDepth, solutionDepth, uniqueSolsDepth, \
      longestSolvesDict, uniqueDistributionDict, completionData, \
      solFindSeconds)
  else:
    secsSearching, minsSearching = getTimeRunning(startTime, endTime)

    print(f"""
          Finished search algorithm:

            Overall:
            {solveMethod                  }\t   Solving method
            {numResets + 1                }\t   Num solutions attempted
            {minSolution._numMoves if minSolution else "--"}\t   Shortest Solution
            {minSolutionUpdates           }\t   Min solution updates
            {numSolutionsAbandoned        }\t   Num solutions abandoned

            Since last reset:
            {secsSearching                }\t   Seconds searching
            {minsSearching                }\t   Minutes searching
            {numIterations                }\t   Num iterations
            {len(q)                       }\t   Ending queue length
            {maxQueueLength               }\t   Max queue length
            {numDeadEnds                  }\t   Num dead ends
            {numPartialSolutionsGenerated }\t   Partial solutions generated
            {numDuplicateGames            }\t   Num duplicate games
            {len(computed)                }\t   Num states computed
          """)

    if minSolution:
      print(f"Found solution{' to level ' + game.level if game.level else ''}!")
      minSolution.printMoves()
    else:
      print("Cannot not find solution.")

    if game.level:
      saveGame(game)

  pass
def shouldSearchBFS() -> bool:
  if SOLVE_METHOD == "BFS" or SOLVE_METHOD == "MIX":
    return True
  elif SOLVE_METHOD == "DFS" or SOLVE_METHOD == "DFR":
    return False
  else:
    raise Exception("Unrecognized solve method: " + SOLVE_METHOD)
def testSolutionPrints(solution: "Game"):
  # Requires that the solution have at least 10 moves to solve
  solution.getNthParent(10).printMoves()
  solution.getNthParent(5).printMoves()
  solution.getNthParent(2).printMoves()
  solution.getNthParent(0).printMoves()
def getTimeRunning(startTime: float, endTime: float) -> tuple[float, float]: # (seconds, minutes)
  seconds = round(endTime - startTime, 1)
  minutes = round((endTime - startTime) / 60, 1)
  return (seconds, minutes)
def analyzeCounterDictionary(dict: defaultdict[int]) -> tuple[int, int, int, int]: # (min, max, mode, total)
  minKey = min(dict.keys())
  maxKey = max(dict.keys())
  totalOccurrences = sum(dict.values())

  # Compute mode
  modeKey = None
  modeKeyOccurrences = 0
  for key, occurrences in dict.items():
    if occurrences > modeKeyOccurrences:
      modeKey = key
      modeKeyOccurrences = occurrences

  return (minKey, maxKey, modeKey, totalOccurrences)
def fPercent(num: float, den: float, roundDigits=1) -> str:
  if den == 0: return "--%"
  return str(round(num/den*100, roundDigits)) + "%"


def readGameInput(userInteracting: bool) -> Game:
  game = _readGame(input, userInteraction=userInteracting)
  game.modified = True
  return game
def readGameFile(gameFileName: str, level: str = None) -> Game:
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

def chooseInteraction():
  validModes = set("psqin")
  mode: str = None
  level: str = None
  userInteracting = True
  originalGame: Game = None
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
    gameFileName = generateFileName(level)
    originalGame = readGameFile(gameFileName, level)

  if originalGame and level:
    originalGame.level = level


  # Fallback to reading in manually
  if not originalGame:
    originalGame = readGameInput(userInteracting)
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

def setSolveMethod(method: str) -> bool:
  method = method.upper()
  if method not in VALID_SOLVE_METHODS:
    print(f"Solve method '{method}' is not a valid input. Choose one of the following instead: " + ", ".join(VALID_SOLVE_METHODS))
    return False

  global SOLVE_METHOD
  global SHUFFLE_NEXT_MOVES
  global DFR_SEARCH_ATTEMPTS

  SOLVE_METHOD = method
  if method == "DFR":
    SHUFFLE_NEXT_MOVES = True
  else:
    DFR_SEARCH_ATTEMPTS = 0

  print("Set solve method to " + method)
  return True

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
