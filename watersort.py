from collections import deque, defaultdict;
import copy;
import itertools;

NUM_SPACES_PER_VIAL = 4
DEBUG_ONLY = False


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
11      10      dg        Dark Green
12      11      b         Blue
                ?         Unknown
                -         Empty
'''

Move = tuple[int, int]
class Game:
  vials: list[deque[str]]
  __numVials: int
  move: Move # The move applied to the parent that got us here
  __isRoot: bool
  prev: "Game" # Original has no root
  root: "Game" # Original has no root
  level: int

  # Flags set on the static class
  reset = False
  quit = False

  # Flags set on the root game
  error: bool

  @staticmethod
  def Create(vials, error = False) -> "Game":
    return Game(vials, None, None, None, error)

  def __init__(self, vials, move, root, prev, error = False):
    self.vials = copy.deepcopy(vials)
    self.__numVials = len(vials)
    self.move = move
    self.prev = prev
    self.__isRoot = root == None
    self.root = self if self.__isRoot else root
    self.level = 0
    self.error = error

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
    self.root.vials[vialIndex][spaceIndex] = val
    return val
  def requestVal(self, original: "Game", request: str) -> str:
    Game.reset = True # Reset the search to handle this new discovery properly

    original.printVials()
    original.printMoves()

    # Other options start with a dash
    print("Other options:\n" +
          "   -o VIAL SPACE COLOR     to provide other values\n" +
          "   -p or -print            to print the current board\n" +
          "   -s or -save             to save the discovered colors\n" +
          "   -r or -reset            to reset the search algorithm\n" +
          "   -moves                  to print the moves to this point\n" +
          "   -level NUM              to change the level of this game\n" +
          "   -q OR quit              to quit\n" +
          "   -d OR -debug            to see debug info")
    rsp: str
    while True:
      print(request + " (Or see other options above.)")

      rsp = input()
      if not rsp:
        break
      elif rsp == "quit" or rsp[0] == "-":
        if rsp == "-q" or rsp == "-quit" or rsp == "quit":
          quit() # Consider terminating just to menu above us??
        elif rsp == "-p" or rsp == "-print":
          self.printVials()
        elif rsp == "-s" or rsp == "-save":
          saveGame(self.root)
        elif rsp == "-r" or rsp == "-reset":
          Game.reset = True
          return "?"
        elif rsp == "-d" or rsp == "-debug":
          print("Printing debug info")
        elif rsp == "-moves":
          self.printMoves()
        elif rsp.startswith("-level"):
          self.saveNewLevel(rsp)
        elif rsp.startswith("-o"):
          self.saveOtherColor(rsp)
      else:
        break
    return rsp
  def saveOtherColor(self, input: str) -> None:
    flag, o_vial, o_space, color = input.split()
    vial = int(o_vial) - 1
    space = int(o_space) - 1
    self.root.vials[vial][space] = color
    print(f"Saved color '{color}' to vial {o_vial} in slot {o_space}. Continue on.")
  def saveNewLevel(self, input: str) -> None:
    flag, o_level = input.split()
    level = int(o_level)
    self.root.level = level
    print(f"Saved new level ({level}). Continue on.")

  _prevPrintedMoves: deque[Move] = None
  def printMoves(self) -> None:
    # Print all the moves that lead to this game
    lines = deque()

    if not self.move:
      lines.append("None")
      Game._prevPrintedMoves = None
    else:
      curGame = self

      moves = deque()
      while curGame and curGame.move:
        start, end = curGame.move
        # CONSIDER: Who how many squares are moving with this move
        # CONSIDER: Color coding the displayed color
        # CONSIDER: Indicating when a vial is finished
        moves.appendleft(curGame.move)
        lines.appendleft(f"{start+1} -> {end+1} {curGame.__getMoveInfo()}")
        curGame = curGame.prev

      if Game._prevPrintedMoves:
        prevMoves = Game._prevPrintedMoves
        i = 0

        SEPARATOR = "\t\t "
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
    COLOR_WIDTH = 3   # CONSIDER: Make more direct by dynamically figuring the maximum color length
    NUMBER_WIDTH = 2  # Num is always less than NUM_SPACES_PER_VIAL (which is small)
    EXTRA_CHARS = 3   # The number of additional chars in our result string

    info = self.__getMoveInfo()
    if info == None:
      return "".ljust(COLOR_WIDTH + NUMBER_WIDTH + EXTRA_CHARS)
    color, num = str(info[0]), str(info[1])

    return f"({color.ljust(COLOR_WIDTH)} {num.rjust(NUMBER_WIDTH)})"
    pass
  def __getMoveInfo(self) -> (str, int): # (Color moved, num moved) OR None
    if not self.move:
      return None
    colorMoved = self.getTopVialColor(self.move[1])
    numMoved = self.prev.__countOnTop(colorMoved, self.move[0])
    return (colorMoved, numMoved)

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

  def generateNextGames(self) -> list("Game"):
    return [self.spawn(move) for move in self.generateNextMoves()]
  def generateNextMoves(self) -> list[Move]:
    moves = list()
    for start, end in itertools.product(range(self.__numVials), range(self.__numVials)):
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

  while Game.reset and not solution:
    Game.reset = False
    numResets += 1

    # Setup our search
    q: deque[Game] = deque()
    computed: set[Game] = set()
    q.append(game)

    numIterations = 0
    numDeadEnds = 0
    numPartialSolutionsGenerated = 0
    numDuplicateGames = 0
    maxQueueLength = 1

    # CONSIDER: Switching our approach based on the state of the game
    # When we still have unknowns, we should find the shortest path to find an unknown,
    # and continue in that same path until we reach a dead end.
    # This makes it easier for a human to

    # Perform the search
    while q and not solution:
      # Break out
      if Game.reset or Game.quit:
        break

      # current = q.popleft()   # Take from the end, will result in depth-first searching
      current = q.pop()       # Take from the start, will result in breadth-first searching
      numIterations += 1
      hasNextGame = False
      if DEBUG_ONLY: current.printVials()
      if numIterations % 1000 == 0:
        print(f"Checked {numIterations} iterations.")
      if numIterations % 10000 == 0:
        current.requestVal(current, "This is a lot. Are you sure?")

      # Check all next moves
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
      if DEBUG_ONLY:
        for game in q: print(game)
        print(f"Finished first check with {len(q)} queued states and {len(computed)} computed states")

  print(f"""
        Finished search algorithm:
          {numResets                    }\t   Num resets
          {numIterations                }\t   Num iterations
          {len(q)                       }\t   Ending queue length
          {maxQueueLength               }\t   Max queue length
          {numDeadEnds                  }\t   Num dead ends
          {numPartialSolutionsGenerated }\t   Partial solutions generated
          {len(computed)                }\t   Num states computed
        """)

  if solution:
    print("Found solution!")
    solution.printVials()
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


def readGame(userInteraction = False) -> Game:
  if userInteraction: print("How many vials are in this game?")
  numVials = int(input())   # Read num vials
  vials = []

  # Read in the colors
  if userInteraction: print(f"On the next {numVials} lines, please type {NUM_SPACES_PER_VIAL} words representing the colors in each vial from top to bottom.\n"+
                            "  Stopping short of the depth of a vial will fill the remaining spaces with question marks.\n" +
                            "  Type a . (period) to insert a whole row of question marks.\n" +
                            "  Type a blank line to mark the remaining vials as empty.\n")
  emptyRest = False
  i = 0
  while i < numVials:
    i += 1
    if emptyRest:
      vials.append(["-"] * NUM_SPACES_PER_VIAL)
      continue

    if userInteraction: print(f"Vial {i}: ")
    response = input()
    if response == "":
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

  # Analyze the colors represented
  countColors = defaultdict(int)
  for vial, space in itertools.product(range(numVials), range(NUM_SPACES_PER_VIAL)):
    countColors[vials[vial][space]] += 1

  errors = list()
  hasUnknowns = countColors["?"] == 0
  for color, count in countColors.items():
    if color == "?" or color == "-":
      continue

    if userInteraction:
      print(f"Color '{color}' \tappears {count} times")

    if count > NUM_SPACES_PER_VIAL:
      errors.append(f"Color '{color}' appears too many times ({count})!")
    elif count < NUM_SPACES_PER_VIAL and hasUnknowns:
      errors.append(f"Color '{color}' appears too few times ({count})!")

  if len(errors):
    SEPARATOR = "\n  "
    print(f"We found {len(errors)} errors while reading in the data:"
          + SEPARATOR + SEPARATOR.join(errors))


  return Game.Create(vials, error=len(errors) > 0)
def chooseInteraction():
  validModes = set("psqi")
  mode: str = None
  while not mode:
    print("""
          How are we interacting?
          p     play
          s     solve
          i     interact
          q     quit
          d     debug mode
          """)
    response = input().strip()
    if response == "d":
      global DEBUG_ONLY
      DEBUG_ONLY = not DEBUG_ONLY
    elif response in validModes:
      mode = response
    else:
      print(f"Invalid response '{response}'. Try again.")

  if mode == "q":
    quit()

  # Read initial state
  level: int = None
  userInteracting = False
  if mode == "i":
    userInteracting = True
    print("What level is this?")
    level = input()
  originalGame = readGame(userInteraction=userInteracting)
  if level != None:
    originalGame.level = level

  if originalGame.error:
    saveGame(originalGame)
    print("Aborting because of errors in the game. Try reviewing the saved file, and resubmitting.")
    return


  # Choose mode
  if mode == "p":
    playGame(originalGame)
  elif mode == "i":
    saveGame(originalGame)
    solveGame(originalGame)
  elif mode == "s":
    solveGame(originalGame)
  else:
    return

def saveGame(game: "Game") -> None:
  fileName = generateFileName(game.level)
  result = generateFileContents(game)
  saveFileContents(fileName, result)
  print(f"Saved discovered game state to file: {fileName}")
def generateFileName(levelNum: int) -> str:
  return f"watersort{levelNum}.txt"
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
