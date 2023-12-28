from collections import defaultdict, deque
from copy import deepcopy
import itertools

from personal.watersort.file import saveGame


NUM_SPACES_PER_VIAL = 4


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
    self.vials = deepcopy(vials)
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
  def __getMoveInfo(self) -> tuple[str, int]: # (colorMoved, numMoved, isComplete) OR None
    if not self.move:
      return None
    start, end = self.move

    colorMoved = self.getTopVialColor(end)
    _, _, numMoved, _ = self.prev.__countOnTop(colorMoved, start)
    complete, _, _, _ = self.__countOnTop(colorMoved, end)

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
  def __prepareMove(self, startVial, endVial) -> tuple[bool, str, str, int, bool]: # (valid, startColor, endColor, endSpace, willComplete)
    INVALID_MOVE = (False, None, None, None, False)
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
    endIsComplete, endOnlyColor, endNumOnTop, endEmptySpaces = self.__countOnTop(endColor, endVial)
    if endEmptySpaces == 0:
      return INVALID_MOVE # End vial is full

    # Verify that this vial isn't full
    startIsComplete, startOnlyColor, startNumOnTop, startEmptySpaces = self.__countOnTop(startColor, startVial)
    if startIsComplete:
      return INVALID_MOVE # Start is fully filled
    if startOnlyColor and endColor == "-":
      return INVALID_MOVE # Don't needlessly switch to a different empty container
    if startNumOnTop > endEmptySpaces:
      # CONSIDER: This may not actually be an invalid move
      return INVALID_MOVE # Only pour when it can all be received

    # Compute additional fields
    willComplete = endOnlyColor and startNumOnTop == endEmptySpaces

    # It's valid
    return (True, startColor, endColor, endEmptySpaces, willComplete)
  # topColor SHOULD NOT be "-" or "?"
  def __countOnTop(self, topColor: str, vialIndex: int) -> tuple[bool, bool, int, int]: # (isComplete, isOnlyColorInColumn, numOfColorOnTop, numEmptySpaces)
    isComplete = True
    onlyColor = True
    emptySpaces = 0
    numOnTop = 0

    vial = self.vials[vialIndex]
    emptySpaceVal = 1 # We only want to count empty spaces that appear BEFORE colors
    for i in range(NUM_SPACES_PER_VIAL):
      color = vial[i]
      if color == "-":
        emptySpaces += emptySpaceVal
      if color != topColor:
        isComplete = False
        if color != "-":
          onlyColor = False
          emptySpaceVal = 0
      elif onlyColor:
        numOnTop += 1

    return (isComplete, onlyColor, numOnTop, emptySpaces)

  def makeMove(self, startVial, endVial) -> bool:
    valid, startColor, endColor, endSpaces, willComplete = self.__prepareMove(startVial, endVial)
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

    emptyValid = [True]*self.__numVials
    moveValid = [True]*self.__numVials
    for start, end in itertools.product(range(self.__numVials), range(self.__numVials)):
      if Game.reset:
        return list()

      # We hope to restrict some moves that are legally valid, but expand the search space unnecessarily
      # Only allow each move to end up in the first empty vial, other empty vials are not allowed
      # If there are two ways to complete a vial, only allow the first way
      # CONSIDER: If this vial can move into a vial that already has only this color in it (but is not empty),
      # That should be the only valid move for this vial

      # We already decided that this vial doesn't have any legal moves
      if not moveValid[start]:
        continue

      valid, startColor, endColor, endEmptySpaces, willComplete = self.__prepareMove(start, end)

      # Obviously, this isn't a valid move
      if not valid:
        continue

      # Only allow the first move into an empty vial from a given start vial
      if endColor == "-":
        if emptyValid[start]:
          emptyValid[start] = False
        else:
          continue
      elif willComplete:
        # If there is a move that will complete a color in a vial, then moving from that vial
        # is never valid. Either, it would attempt to complete the other direction OR  it would
        # only move into an empty vial. Obviously, there are no other colors for it to land on.
        moveValid[end] = False

      # Fine, it's valid
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
