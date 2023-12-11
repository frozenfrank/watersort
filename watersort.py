from collections import deque, defaultdict
from time import time;
from typing import Callable;
import copy;
import itertools;
import sys;

NUM_SPACES_PER_VIAL = 4
DEBUG_ONLY = False
FORCE_SOLVE_LEVEL = None # "100"


SOLVE_METHOD = "MIX" # "BFS", "DFS", "MIX"
MIX_SWITCH_THRESHOLD_MOVES = 10
ENABLE_QUEUE_CHECKS = False # Disable only for temporary testing
DENSE_QUEUE_CHECKING = True
REPORT_ITERATION_FREQ = 10000 if SOLVE_METHOD == "BFS" else 1000
QUEUE_CHECK_FREQ = REPORT_ITERATION_FREQ * 10


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
    if not val or val == "":
      val = "?"
    else:
      Game.reset = True # Reset the search to handle this new discovery properly
      self.root.modified = True
      self.root.vials[vialIndex][spaceIndex] = val

    return val
  def requestVal(self, original: "Game", request: str) -> str:
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
          return "?"

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
      lines.append(f"  {color}: \t{count}")

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
def solveGame(game: "Game"):
  # Intelligent search through all the possible game states until we find a solution.
  # The game already handles asking for more information as required

  solution: Game = None
  numResets = -1
  Game.reset = True

  startTime: float = None
  endTime: float = None

  while Game.reset and not solution:
    Game.reset = False
    numResets += 1

    # First correct any errors in the game
    game.attemptCorrectErrors()

    startTime = time()

    # Setup our search
    q: deque[Game] = deque()
    computed: set[Game] = set()
    q.append(game)
    searchBFS: bool = SOLVE_METHOD != "DFS"

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
      if numIterations % REPORT_ITERATION_FREQ == 0:
        print(f"Checked {numIterations} iterations.")

        if SOLVE_METHOD == "MIX" and current._numMoves >= MIX_SWITCH_THRESHOLD_MOVES:
          searchBFS = False
          print("Switching to DFS search for MIX solve method")

        if numIterations % QUEUE_CHECK_FREQ == 0:
          if ENABLE_QUEUE_CHECKS and SOLVE_METHOD != "BFS":
            current.requestVal(current, "This is a lot. Are you sure?")
          else:
            print(f"QUEUE CHECK: \titrs: {numIterations} \tmvs: {current._numMoves} \tq len: {len(q)} \tends: {numDeadEnds} \tdup games: {numDuplicateGames} \tmins: {round((time() - startTime) / 60, 1)}")

      # Check all next moves
      hasNextGame = False
      for nextGame in current.generateNextGames():
        numPartialSolutionsGenerated += 1
        if nextGame in computed:
          numDuplicateGames += 1
          continue
        computed.add(nextGame)
        hasNextGame = True
        if (nextGame.isFinished()):
          solution = nextGame
          break
        else:
          # NOTE: We may be re-computing things expensively with alternative paths to the same game state
          # It would be better to memoize the game states with a custom hash function to avoid this,
          # But i don't expect it to make a large difference in this context. Order really matters here.
          q.append(nextGame)

      # Maintain stats
      maxQueueLength = max(maxQueueLength, len(q))
      if not hasNextGame:
        numDeadEnds += 1

  endTime = time()
  secsSearching = round(endTime - startTime, 1)
  minsSearching = round((endTime - startTime) / 60, 1)
  print(f"""
        Finished search algorithm:
          {SOLVE_METHOD                 }\t   Solving method
          {numResets                    }\t   Num resets
          {secsSearching                }\t   Seconds searching since last reset
          {minsSearching                }\t   Minutes searching since last reset
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
    # solution.printVials()
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

  # Allow different forms of level override
  if FORCE_SOLVE_LEVEL:
    # DEBUG
    level = FORCE_SOLVE_LEVEL
    mode = "i"
    print(f"FORCING SOLVE LEVEL to {level}")
  elif len(sys.argv) == 2:
    # COMMAND LINE
    level = sys.argv[1]
    mode = "i"

  # Request the mode
  while not mode:
    print("""
          How are we interacting?
          NAME  level name
          p     play
          s     solve (from new input)
          i     interact (or resume an existing game)
          q     quit
          d     debug mode
          """)
    response = input().strip()
    if response == "d":
      global DEBUG_ONLY
      DEBUG_ONLY = not DEBUG_ONLY
    elif response in validModes:
      mode = response
      if mode == "i":
        userInteracting = False
    else:
      level = response
      mode = "i"

  if mode == "q":
    quit()

  # Read initial state
  if (mode == "i" or mode == "s") and not level:
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
    solveGame(originalGame)
    saveGame(originalGame)
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
def generateFileName(levelNum: str) -> str:
  return f"wslevels/{levelNum}.txt"
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

# Run the program!
chooseInteraction()
