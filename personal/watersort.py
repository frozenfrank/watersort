from collections import deque, defaultdict
import random
from time import time;
from typing import Callable;
import copy;
import itertools;
import sys;

SOLVER_VERSION = 1
ANALYZER_VERSION = 2

NUM_SPACES_PER_VIAL = 4
DEBUG_ONLY = False
FORCE_SOLVE_LEVEL = None # "100"


SOLVE_METHOD = "MIX"
VALID_SOLVE_METHODS = set(["MIX", "BFS", "DFS"]) # An enum is more accurate, but overkill for this need

MIX_SWITCH_THRESHOLD_MOVES = 10
ENABLE_QUEUE_CHECKS = True # Disable only for temporary testing
DENSE_QUEUE_CHECKING = True

SHUFFLE_NEXT_MOVES = False
ANALYZE_ATTEMPTS = 100

'''
COLORS
Num     Index   Code      Name
1       0       m         Mint
2       1       g         Gray
3       2       o         Orange
4       3       y         Yellow
5       4       r         Red
6       5       p         Purple
7       6       pk        Puke
8       7       pn        Pink
9       8       br        Brown
10      9       lb        Light Blue
11      10      gn        Dark Green
12      11      b         Blue
                ?         Unknown
                -         Empty
'''

Vials = list[list[str]]
Move = tuple[int, int]
class Game:
  vials: Vials
  __numVials: int
  move: Move # The move applied to the parent that got us here
  _numMoves: int
  __isRoot: bool
  prev: "Game" # Original has no root
  root: "Game" # Original has no root

  # Flags set on the static class
  reset = False
  quit = False

  # Flags set on the root game
  level: str
  modified: bool # Indicates it's changed from the last read in state
  _colorError: bool
  _hasUnknowns: bool

  # Cached for single use calculation
  COMPLETE_STR = " complete"
  COLOR_WIDTH = 3             # CONSIDER: Make more direct by dynamically figuring the maximum color length
  NUMBER_WIDTH = 1            # Num is always less than NUM_SPACES_PER_VIAL (which is small)
  EXTRA_CHARS = 3             # The number of additional chars in our result string
  TOTAL_MOVE_PRINT_WIDTH = COLOR_WIDTH + NUMBER_WIDTH + EXTRA_CHARS + len(COMPLETE_STR)

  @staticmethod
  def Create(vials) -> "Game":
    newGame = Game(vials, None, None, None)
    newGame._analyzeColors()
    return newGame

  def __init__(self, vials: "Vials", move: "Move", root: "Game", prev: "Game", modified = False):
    self.vials = copy.deepcopy(vials)
    self.__numVials = len(vials)
    self.move = move
    self.prev = prev
    self.__isRoot = root == None
    self.root = self if self.__isRoot else root
    self._numMoves = 0 if self.__isRoot else prev._numMoves + 1
    self.modified = modified

  # Returns the nth-parent of the game,
  # or None if n is greater than the number of parents
  def getNthParent(self, n: int) -> "Game":
    out = self
    for _ in range(n):
      if out.prev:
        out = out.prev
      else:
        return None
    return out
  def hasError(self) -> bool:
    return self._colorError # Or other errors
  # Attempts to correct any errors, and then returns a bool indicating if errors still exist
  def attemptCorrectErrors(self) -> bool:
    if not self.hasError():
      return False

    self.requestVal(self, "The colors aren't right in this game. Fix them, and press enter to proceed.")
    self._analyzeColors()
    if self.hasError():
      saveGame(self, forceSave=True)
      print("Things still aren't right. Review the saved file, and try again.")
      quit()
      return True
    else:
      print("Issues resolved. Proceeding.")
      return False

  def getTopVialColor(self, vialIndex) -> str:
    vial = self.vials[vialIndex]
    for i in range(NUM_SPACES_PER_VIAL):
      val = vial[i]
      if val == '?':
        vial[i] = self.getColor(vialIndex, i)
        return vial[i]
      elif val == '-':
        continue
      else:
        return val
    return "-"

  def getColor(self, vialIndex, spaceIndex):
    val = self.vials[vialIndex][spaceIndex]
    if val != '?':
      return val
    if self.__isRoot:
      return self.tryAccessVal(self, vialIndex, spaceIndex)
    else:
      rootVal = self.root.tryAccessVal(self, vialIndex, spaceIndex)
      if not rootVal:
        return "?"
      self.vials[vialIndex][spaceIndex] = rootVal
      return rootVal
  # The following two methods to be called on `self.root` only
  def tryAccessVal(self, original: "Game", vialIndex, spaceIndex) -> str:
    val = self.vials[vialIndex][spaceIndex]
    if val != "?":
      return val

    print("\n\nDiscovering new value:")
    startVial = vialIndex + 1
    request = f"What's the new value in the {startVial} vial?"
    val = self.requestVal(original, request)
    if val:
      Game.reset = True # Reset the search to handle this new discovery properly
      self.root.modified = True
      self.root.vials[vialIndex][spaceIndex] = val

    return val
  def requestVal(self, original: "Game", request: str, printState = True) -> str:
    if printState:
      original.printVials()
      original.printMoves()

    # Other options start with a dash
    print("Other options:\n" +
          "   -o VIAL SPACE COLOR     to provide other values\n" +
          "   -p or -print            to print the ROOT board\n" +
          "   -pc                     to print the CURRENT board\n" +
          "   -c or -colors           to print the distribution of colors in the vials\n" +
          "   -s or -save             to save the discovered colors\n" +
          "   -r or -reset            to reset the search algorithm\n" +
          "   -m OR -moves            to print the moves to this point\n" +
          "   -level NUM              to change the level of this game\n" +
          "   -vials NUM              to change the number of vials in the game\n" +
          "   -e OR -exit             to save and exit\n" +
          "   -q OR quit              to quit\n" +
          "   -d OR -debug            to see debug info")
    rsp: str
    while True:
      print(request + " (Or see other options above.)")

      rsp = input()
      if not rsp:
        # CONSIDER: This may not actually be the best behavior
        break
      elif rsp == "quit" or rsp[0] == "-":
        root = self.root

        # Program mechanics
        if rsp == "-q" or rsp == "-quit" or rsp == "quit":
          quit() # Consider terminating just to menu above us??
        elif rsp == "-e" or rsp == "-exit":
          saveGame(root)
          quit()
        elif rsp == "-s" or rsp == "-save":
          saveGame(root, forceSave=True)
        elif rsp == "-r" or rsp == "-reset":
          Game.reset = True
          return ""

        # Printing status
        elif rsp == "-p" or rsp == "-print":
          root.printVials()
        elif rsp == "-pc":
          original.printVials()
        elif rsp == "-m" or rsp == "-moves":
          original.printMoves()
        elif rsp == "-d" or rsp == "-debug":
          print("Printing debug info... (None)")
          # TODO: Print the queue length, and other search related stats
        elif rsp == "-c" or rsp == "-colors" or rsp == "-color":
          root.printColors()

        # Special commands
        elif rsp.startswith("-level"):
          root.saveNewLevel(rsp)
        elif rsp.startswith("-o"):
          root.saveOtherColor(rsp)
        elif rsp.startswith("-v"):
          root.saveNewVials(rsp)

        # Default
        else:
          print("Unrecognized command: " + rsp)
      else:
        # They answered the original question
        break

    return rsp
  def saveOtherColor(self, input: str) -> None:
    flag, o_vial, o_space, color = input.split()
    vial = int(o_vial) - 1
    space = int(o_space) - 1
    Game.reset = True
    self.root.modified = True
    self.root.vials[vial][space] = color
    print(f"Saved color '{color}' to vial {o_vial} in slot {o_space}. Continue on.")
  def saveNewLevel(self, input: str) -> None:
    flag, o_level = input.split()
    self.root.level = o_level
    self.root.modified = True
    print(f"Saved new level ({o_level}). Continue on.")
  def saveNewVials(self, input: str) -> None:
    flag, o_vials = input.split()
    numVials = int(o_vials)
    if numVials > len(self.vials):
      self.modified = True
      Game.reset = True
      while numVials > len(self.vials):
        self.vials.append(["-"] * NUM_SPACES_PER_VIAL)
      print(f"Increased number of vials to {numVials}")
    elif numVials < len(self.vials):
      self.modified = True
      Game.reset = True
      self.vials = self.vials[0:numVials]
      print(f"Truncated the vials to only the first {numVials}")
    else:
      print(f"No change to number of vials. Still have {numVials}")
    self.__numVials = numVials


  _prevPrintedMoves: deque[Move] = None
  def printMoves(self) -> None:
    # Print all the moves that lead to this game
    lines = deque()

    if not self.move:
      lines.append("None")
      Game._prevPrintedMoves = None
    else:
      curGame = self
      SEPARATOR = "\t "

      moves = deque()
      while curGame and curGame.move:
        start, end = curGame.move
        # CONSIDER: Color coding the displayed color
        moves.appendleft(curGame.move)
        moveString = f"{start+1}->{end+1}".ljust(8)
        lines.appendleft(moveString + curGame.__getMoveString())
        curGame = curGame.prev

      if Game._prevPrintedMoves:
        prevMoves = Game._prevPrintedMoves
        i = 0

        while i < len(prevMoves) and i < len(moves):
          if moves[i] == prevMoves[i]:
            lines[i] += SEPARATOR + "(same)"
          else:
            lines[i] += SEPARATOR + "(different)"
            break
          i += 1

      Game._prevPrintedMoves = moves

    NEW_LINE = "\n  "
    print(f"Moves ({len(lines)}):" + NEW_LINE + NEW_LINE.join(lines))
  def printVials(self) -> None:
    lines = [list() for _ in range(NUM_SPACES_PER_VIAL + 1)]

    for i in range(self.__numVials):
      lines[0].append("\t" + str(i + 1))

    for spaceIndex in range(NUM_SPACES_PER_VIAL):
      for vialIndex in range(self.__numVials):
        lines[spaceIndex + 1].append("\t" + self.vials[vialIndex][spaceIndex])

    print("\n".join(["".join(line) for line in lines]))
  def __getMoveString(self) -> str:

    info = self.__getMoveInfo()
    result: str
    if info == None:
      result = ""
    else:
      color, num, complete = info
      completeStr = Game.COMPLETE_STR if complete else ""
      result = f"({num} {color}{completeStr})"

    return result.ljust(Game.TOTAL_MOVE_PRINT_WIDTH)
  def __getMoveInfo(self) -> (str, int): # (colorMoved, numMoved, isComplete) OR None
    if not self.move:
      return None
    start, end = self.move

    colorMoved = self.getTopVialColor(end)
    _, _, numMoved = self.prev.__countOnTop(colorMoved, start)
    complete, _, _ = self.__countOnTop(colorMoved, end)

    return (colorMoved, numMoved, complete)
  # Prints out the state of the colors, including any errors
  def printColors(self, analyzedData = None) -> list[str]:
    lines = []
    countColors, errors = analyzedData if analyzedData else self._analyzeColors()

    lines.append("Frequency of colors:")
    for color, count in sorted(countColors.items()):
      if color == "-": continue
      label = "\t"
      if color != "?" and count != NUM_SPACES_PER_VIAL:
        label += "(too many)" if count > NUM_SPACES_PER_VIAL else "(too few)"
      lines.append(f"  {color}: \t{count}" + label)

    if len(errors):
      lines.append("\nErrors:")
      for error in errors:
        lines.append("  " + error)

    print("\n".join(lines))
  def _analyzeColors(self) -> tuple[dict[str, int], list[str]]: # (dict[color, occurrences], list[error strings])

    # Analyze the colors represented
    countColors = defaultdict(int)
    for vial, space in itertools.product(self.vials, range(NUM_SPACES_PER_VIAL)):
      countColors[vial[space]] += 1

    errors = list()
    hasUnknowns = countColors["?"] == 0
    for color, count in countColors.items():
      if color == "?" or color == "-":
        continue

      if count > NUM_SPACES_PER_VIAL:
        errors.append(f"Color '{color}' appears too many times ({count})!")
      elif count < NUM_SPACES_PER_VIAL and hasUnknowns:
        errors.append(f"Color '{color}' appears too few times ({count})!")

    self.root._hasUnknowns = hasUnknowns
    self.root._colorError = len(errors) > 0
    return (countColors, errors)
  def printVialsDense(self) -> None:
    out = list()
    for vial, space in itertools.product(range(self.__numVials), range(NUM_SPACES_PER_VIAL)):
      out.append(self.vials[vial][space].ljust(2))
    print("".join(out))


  def isFinished(self) -> bool:
    for vial in self.vials:
      c0 = vial[0]
      for c in vial:
        if c == "?":  return False
        if c != c0:   return False

    return True
  def canMove(self, startVial, endVial) -> bool:
    return self.__prepareMove(startVial, endVial)[0]
  def __prepareMove(self, startVial, endVial) -> (bool, str, str, int): # (valid, startColor, endColor, endSpace)
    INVALID_MOVE = (False, None, None, None)
    if startVial == endVial:
      return INVALID_MOVE # Can't move to the same place
    if self.move and startVial == self.move[1] and endVial == self.move[0]:
      return INVALID_MOVE # Can't simply undo the previous move

    startColor = self.getTopVialColor(startVial)
    if startColor == "-" or startColor == "?":
      return INVALID_MOVE # Can only move an active color
    endColor = self.getTopVialColor(endVial)
    if endColor != "-" and endColor != startColor:
      return INVALID_MOVE # Can only place on the same color, or an empty square

    # Verify the destination vial
    endSpaces = 0
    for i in range(NUM_SPACES_PER_VIAL):
      if self.vials[endVial][i] == '-':
        endSpaces += 1
      else:
        break
    if endSpaces == 0:
      return INVALID_MOVE # End vial is full

    # Verify that this vial isn't full
    isComplete, onlyColor, numOnTop = self.__countOnTop(startColor, startVial)
    if isComplete:
      return INVALID_MOVE # Start is fully filled
    if onlyColor and endColor == "-":
      return INVALID_MOVE # Don't needlessly switch to a different empty container
    if numOnTop > endSpaces:
      # CONSIDER: This may not actually be an invalid move
      return INVALID_MOVE # Only pour when it can all be received

    # It's valid
    return (True, startColor, endColor, endSpaces)
  # topColor SHOULD NOT be "-" or "?"
  def __countOnTop(self, topColor: str, vialIndex: int) -> (bool, bool, int): # (isComplete, isOnlyColorInColumn, numOfColorOnTop)
    isComplete = True
    onlyColor = True
    numOnTop = 0

    vial = self.vials[vialIndex]
    for i in range(NUM_SPACES_PER_VIAL):
      color = vial[i]
      if color != topColor:
        isComplete = False
        if color != "-":
          onlyColor = False
      elif onlyColor:
        numOnTop += 1

    return (isComplete, onlyColor, numOnTop)

  def makeMove(self, startVial, endVial) -> bool:
    valid, startColor, endColor, endSpaces = self.__prepareMove(startVial, endVial)
    if not valid:
      return False

    # Remove up to that many colors from start
    i = 0
    moveRange = endSpaces
    startColors = 0
    while i < moveRange and i < NUM_SPACES_PER_VIAL:
      color = self.vials[startVial][i]
      if color == '-':
        moveRange += 1
      elif color == startColor:
        startColors += 1
        self.vials[startVial][i] = "-"
      else:
        break
      i += 1

    # Add the values back to endVial, from the bottom
    i = NUM_SPACES_PER_VIAL - 1
    moveRange = startColors
    while i >= 0 and moveRange > 0:
      color = self.vials[endVial][i]
      if color == '-':
        moveRange -= 1
        self.vials[endVial][i] = startColor
      i -= 1

    # Finish
    return True

  def spawn(self, move: Move) -> "Game":
    newGame = Game(self.vials, move, self.root, self)
    newGame.makeMove(move[0], move[1])
    return newGame

  def generateNextGames(self) -> list["Game"]:
    return [self.spawn(move) for move in self.generateNextMoves()]
  def generateNextMoves(self) -> list[Move]:
    moves = list()
    for start, end in itertools.product(range(self.__numVials), range(self.__numVials)):
      if Game.reset:
        return list()
      if self.canMove(start, end):
        moves.append((start, end))
    return moves

  def __str__(self) -> str:
    out = list()
    for vial, space in itertools.product(range(self.__numVials), range(NUM_SPACES_PER_VIAL)):
      out.append(self.vials[vial][space])
    return "".join(out)
  def __eq__(self, other: object) -> bool:
    """Overrides the default implementation"""
    if isinstance(other, Game):
        return self.__str__() == other.__str__()
    return False
  def __hash__(self) -> int:
    return hash(self.__str__())

def playGame(game: "Game"):
  currentGame = game
  print("""
        Play the game:
        r         reset
        q         quit
        NUM NUM   move from vial to vial
        """)
  while True:
    currentGame.printMoves()
    currentGame.printVials()
    read = input()
    if not read:
      continue
    elif read == "q":
      break
    elif read == "r":
      currentGame = game
      continue
    read1, read2 = read.split()

    startVial, endVial = int(read1) - 1, int(read2) - 1
    if not currentGame.canMove(startVial, endVial):
      print("That move is invalid")
      continue

    # Perform the move
    currentGame = currentGame.spawn((startVial, endVial))

  print("Goodbye.")
def solveGame(game: "Game", solveMethod = "MIX", analyzeSampleCount = 0):
  # Intelligent search through all the possible game states until we find a solution.
  # The game already handles asking for more information as required

  solution: Game = None
  numResets = 0

  analysisStart: float = time()
  startTime: float = None
  endTime: float = None

  REPORT_ITERATION_FREQ = 10000 if solveMethod == "BFS" else 1000
  QUEUE_CHECK_FREQ = REPORT_ITERATION_FREQ * 10

  # Analyzing variables
  partialDepth = defaultdict(int)
  dupGameDepth = defaultdict(int)
  deadEndDepth = defaultdict(int)
  solutionDepth = defaultdict(int)
  uniqueSolsDepth = defaultdict(int)
  solFindSeconds = defaultdict(int)
  uniqueSolutions: set["Game"] = set()
  isUniqueList: list[bool] = list()
  analysisSamplesRemaining = analyzeSampleCount
  lastReportTime = 0
  REPORT_SEC_FREQ = 15

  # Temp only
  timeCheck: float

  while Game.reset or not solution or analysisSamplesRemaining > 0:
    if Game.reset:
      Game.reset = False
      numResets += 1
    elif analysisSamplesRemaining > 0:
      timeCheck = time()
      if analysisSamplesRemaining % 1000 == 0 or timeCheck - lastReportTime > REPORT_SEC_FREQ:
        print(f"Searching for {analysisSamplesRemaining} more solutions. Running for {round(timeCheck - analysisStart, 1)} seconds. ")
        lastReportTime = timeCheck
      analysisSamplesRemaining -= 1
      solution = None


    # First correct any errors in the game
    game.attemptCorrectErrors()

    startTime = time()

    # Setup our search
    q: deque["Game"] = deque()
    computed: set["Game"] = set()
    q.append(game)
    searchBFS: bool = solveMethod != "DFS"

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

        if solveMethod == "MIX" and current._numMoves >= MIX_SWITCH_THRESHOLD_MOVES:
          searchBFS = False
          print("Switching to DFS search for MIX solve method")

        if numIterations % QUEUE_CHECK_FREQ == 0:
          if ENABLE_QUEUE_CHECKS and not searchBFS:
            current.requestVal(current, "This is a lot. Are you sure?")
          else:
            print(f"QUEUE CHECK: \titrs: {numIterations} \tmvs: {current._numMoves} \tq len: {len(q)} \tends: {numDeadEnds} \tdup games: {numDuplicateGames} \tmins: {round((time() - startTime) / 60, 1)}")
            if solveMethod == "MIX":
              rsp = current.requestVal(current, "This is a lot. Would you like to switch to a faster approach? (Yes/no)", printState=False)
              rsp.lower()
              if rsp and rsp[0] == "y":
                searchBFS = False
                solveMethod = "DFS"
              else:
                pass

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
          if not solution or nextGame._numMoves < solution._numMoves:
            solution = nextGame
          solutionDepth[solution._numMoves] += 1
          timeCheck = time()
          solFindSeconds[int((timeCheck - startTime + 0.9) // 1)] += 1
          if solution not in uniqueSolutions:
            uniqueSolutions.add(solution)
            uniqueSolsDepth[solution._numMoves] += 1
            isUniqueList.append(True)
          else:
            isUniqueList.append(False)
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
    minSolutionMoves, maxSolutionMoves, modeSolutionMoves, countUniqueSols = analyzeCounterDictionary(uniqueSolsDepth)
    minDeadEnd, lastDeadEnd, modeDeadEnds, _ = analyzeCounterDictionary(deadEndDepth)
    nDupSols = analyzeSampleCount - countUniqueSols
    minFindTime, modeFindTime, maxFindTime, _ = analyzeCounterDictionary(solFindSeconds);

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

    # Identify and prepare some extra data
    extraDataLen = identifyExtraDataLength(partialDepth)
    longestSolvesDict = prepareLongestSolves(extraDataLen, solFindSeconds)
    uniqueDistributionDict = prepareUniqueDistribution(extraDataLen, isUniqueList)

    saveAnalysisResults(\
      game.level, endTime - analysisStart, analyzeSampleCount, \
      partialDepth, dupGameDepth, deadEndDepth, solutionDepth, uniqueSolsDepth, \
      longestSolvesDict, uniqueDistributionDict, solFindSeconds)
  else:
    secsSearching, minsSearching = getTimeRunning(startTime, endTime)

    print(f"""
          Finished search algorithm:

            Overall:
            {solveMethod                  }\t   Solving method
            {numResets                    }\t   Num resets

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

    if solution:
      print("Found solution!")
      solution.printMoves()
    else:
      print("Cannot not find solution.")

    if game.level:
      saveGame(game)

  pass
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
def analyzeCounterDictionary(dict: defaultdict[int]) -> tuple[int, int, int]: # (min, max, mode, total)
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
def readGameFile(gameFileName: str) -> Game:
  gameRead: Game = None
  try:
    gameFile = open(gameFileName, "r")
    nextLine = lambda: gameFile.readline().strip()

    nextLine()                      # Skip mode
    level = nextLine()              # Read level name
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
  validModes = set("psqi")
  mode: str = None
  level: str = None
  userInteracting = True
  originalGame: Game = None
  analyzeSamples = ANALYZE_ATTEMPTS

  # Allow different forms of level override
  if FORCE_SOLVE_LEVEL:
    # DEBUG
    level = FORCE_SOLVE_LEVEL
    mode = "i"
    print(f"FORCING SOLVE LEVEL to {level}")
  elif len(sys.argv) > 1:
    # COMMAND LINE
    level = sys.argv[1]
    mode = "i"

  # Read solve method from command line
  if len(sys.argv) > 2:
    setSolveMethod(sys.argv[2])

  # Request the mode
  while not mode:
    print("""
          How are we interacting?
          NAME                      level name
          p                         play
          s                         solve (from new input)
          i                         interact (or resume an existing game)
          a SAMPLES? LEVEL?         analyze
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
        analyzeSamples = int(words[1])
      if len(words) > 2:
        level = words[2]
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
  if (mode == "i" or mode == "s" or mode == "a") and not level:
    if userInteracting:
      print("What level is this?")
    level = input()

  # Attempt to read the game state out of a file
  if mode != "s" and level:
    gameFileName = generateFileName(level)
    originalGame = readGameFile(gameFileName)

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
    playGame(originalGame)
  elif mode == "i" or mode == "s":
    solveGame(originalGame, solveMethod=SOLVE_METHOD)
    saveGame(originalGame)
  elif mode == "a":
    global SHUFFLE_NEXT_MOVES
    SHUFFLE_NEXT_MOVES = True
    solveGame(originalGame, solveMethod="DFS", analyzeSampleCount=analyzeSamples)
  else:
    print("Unrecognized mode: " + mode)

  quit(0)

def saveGame(game: "Game", forceSave = False) -> None:
  if not forceSave and not game.modified:
    return None # No saving necessary
  fileName = generateFileName(game.level)
  result = generateFileContents(game)
  saveFileContents(fileName, result)
  game.modified = False
  print(f"Saved discovered game state to file: {fileName}")
def getBasePath(absolutePath = True) -> str:
  return "/Users/frozenfrank/Documents/College/Fall 2023/CPC/personal/" if absolutePath else ""
def generateFileName(levelNum: str, absolutePath = True) -> str:
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

def setSolveMethod(method: str) -> bool:
  method = method.upper()
  if method in VALID_SOLVE_METHODS:
    global SOLVE_METHOD
    SOLVE_METHOD = method
    print("Set solve method to " + method)
  else:
    print(f"Solve method '{method}' is not a valid input. Choose one of the following instead: " + ", ".join(VALID_SOLVE_METHODS))

def generateAnalysisResultsName(level: str, absolutePath = True) -> str:
  return getBasePath(absolutePath) + f"wsanalysis/{level}-{round(time())}.csv"
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
  deepestGame = max(partialStatesDepthDict.keys())
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


# Run the program!
# Call signatures:
# py watersort.py LEVEL <MODE>
# py watersort.py LEVEL MIX <Move Threshold>
chooseInteraction()
