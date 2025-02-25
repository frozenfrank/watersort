import signal
from collections import deque, defaultdict
from math import floor, log
import random
from colorama import Fore, Back, Style
from time import time
from typing import Callable
import copy;
import itertools;
import sys;

INSTALLED_BASE_PATH = ""
WRITE_FILES_TO_ABSOLUTE_PATH = False

SOLVER_VERSION = 1
ANALYZER_VERSION = 5

NUM_SPACES_PER_VIAL = 4
DEBUG_ONLY = False
FORCE_SOLVE_LEVEL = None # "263"
FORCE_INTERACTION_MODE = None # "a"


SOLVE_METHOD = "DFR"
VALID_SOLVE_METHODS = set(["MIX", "BFS", "DFS", "DFR"]) # An enum is more accurate, but overkill for this need

MIX_SWITCH_THRESHOLD_MOVES = 10
ENABLE_QUEUE_CHECKS = True # Disable only for temporary testing

SHUFFLE_NEXT_MOVES = False
ANALYZE_ATTEMPTS = 10000
DFR_SEARCH_ATTEMPTS = 200

CONFIRM_APPLY_LAST_UNKNOWN = False
CONFIRM_APPLY_LAST_BATCH_COLOR = False
AUTO_BFS_FOR_UNKNOWNS_ORIG_METHOD = None

RESERVED_COLORS = set(["?", "-"])
FEW_VIALS_THRESHOLD = 7 # I'm not actually sure if this is the right threshold, but it appears correct

COLOR_CODES = defaultdict(str, {
  "m": Back.CYAN,                                 # Mint
  "g": Style.DIM + Back.WHITE,                    # Gray
  "gr": "",                                       # Green (Occasionally)
  "o": Back.YELLOW + Fore.RED,                    # Orange
  "y": Back.YELLOW + Fore.BLACK,                  # Yellow
  "r": Back.RED + Fore.WHITE,                     # Red
  "p": Back.BLACK  + Fore.MAGENTA,                # Purple
  "pk": Back.GREEN + Fore.BLACK,                  # Puke
  "pn": Back.MAGENTA,                             # Pink
  "br": Back.WHITE + Fore.MAGENTA,                # Brown
  "lb": Fore.CYAN + Back.WHITE,                   # Light Blue
  "gn": Back.BLACK + Fore.GREEN,                  # Dark Green
  "b": Back.BLUE + Fore.WHITE,                    # Blue
  "?": "",                                        # Unknown
  "-": "",                                        # Empty
})

Vials = list[list[str]]
Move = tuple[int, int]
class Game:
  vials: Vials
  __numVials: int
  move: Move # The move applied to the parent that got us here
  _numMoves: int
  __isRoot: bool
  prev: "Game" # Original has no prev
  root: "Game"
  completionOrder: list[tuple[str, int]] # (color, depth)[] # Immutable

  # Flags set on the static class
  reset: bool = False
  quit: bool = False
  latest: bool = False # "Game" | None

  # Flags set on the root game
  level: str
  modified: bool # Indicates it's changed from the last read in state
  _colorError: bool
  _hasUnknowns: bool

  # Cached for single use calculation
  COMPLETE_STR = Style.BRIGHT + " complete" + Style.NORMAL
  VACATED_STR = Style.DIM + " vacated" + Style.NORMAL
  STARTED_STR = Style.DIM + " occupied" + Style.NORMAL
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
    self.modified = modified

    self.__isRoot = root == None
    self.root = self if self.__isRoot else root
    self._numMoves = 0 if self.__isRoot else prev._numMoves + 1
    self.completionOrder = list() if self.__isRoot else prev.completionOrder

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
        return self.getColor(vialIndex, i)
      elif val == '-':
        continue
      else:
        return val
    return "-"

  def getColor(self, vialIndex, spaceIndex):
    val = self.vials[vialIndex][spaceIndex]
    if val != '?':
      return val

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

    print("\n\n", end="")
    if SOLVE_METHOD == "DFR":
      resolveWithMethod = "MIX"
      print(f"Unknown value detected with {SOLVE_METHOD} solve method. Re-solving with {resolveWithMethod} to detect unknown values.")
      autoSwitchForUnknownsApply(newState=resolveWithMethod)
      Game.reset = True
      return None # No value requested

    print("Discovering new value:")
    startVial = vialIndex + 1
    request = f"What's the new value in the {startVial} vial?"
    colorDist, colorErrors = self._analyzeColors()
    if colorDist["?"] > 0:
      underusedColors = sorted(self._identifyUnderusedColors(colorDist))
      fewColors = [formatVialColor(color, color) for color in underusedColors]
      request += f" ({colorDist['?']} remaining unknowns: {', '.join(fewColors)})"

    rootChanged = False
    val = self.requestVal(original, request)
    if val:
      rootChanged = True
      Game.latest = self
      self.root.vials[vialIndex][spaceIndex] = val

    colorDist, colorErrors = self.root._analyzeColors()
    underusedColors = self._identifyUnderusedColors(colorDist)

    if colorDist["?"] == 1:
      lastColor = next((k for k, v in colorDist.items() if (v < NUM_SPACES_PER_VIAL and k != "?")), None)
      lastVialIndex, lastVialSpace = self.root._findFirstSpaceWithColor("?")
      lastSpace = formatSpaceRef(lastVialIndex, lastVialSpace)

      request =   "There is only one remaining unknown value."

      proceed = True
      if CONFIRM_APPLY_LAST_UNKNOWN:
        request += f" Would you like to save {formatVialColor(lastColor, lastColor)} into space {lastSpace}?"
        proceed = self.confirmPrompt(original, request)
      else:
        request += f" Saving color {formatVialColor(lastColor, lastColor)} into space {lastSpace}."
        print(request)

      if proceed:
        self.root.vials[lastVialIndex][lastVialSpace] = lastColor
        Game.latest = None # Prevent the solver from attempting BFS on this solved state
        rootChanged = True
    elif colorDist["?"] <= NUM_SPACES_PER_VIAL and len(underusedColors) == 1:
      lastColor = underusedColors[0]
      request = "Only one potential color remains to fill the unknowns."

      proceed = True
      if CONFIRM_APPLY_LAST_BATCH_COLOR:
        request += f" Would you like to save {formatVialColor(lastColor, lastColor)} in *all* {colorDist['?']} spaces?"
        proceed = self.confirmPrompt(original, request)
      else:
        request += f" Saving color {formatVialColor(lastColor, lastColor)} into {colorDist['?']} remaining spaces."
        print(request)

      if proceed:
        Game.latest = None
        for vialIdx, spaceIdx in itertools.product(range(self.__numVials), range(NUM_SPACES_PER_VIAL)):
          if self.root.vials[vialIdx][spaceIdx] == "?":
            self.root.vials[vialIdx][spaceIdx] = lastColor


    colorDist, colorErrors = self.root._analyzeColors()
    if colorDist["?"] == 0:
      rootChanged = True
      print("Reverting to original solve method now that all discovered values are found.")
      autoSwitchForUnknownsRevert()


    if rootChanged:
      Game.reset = True # Reset the search to handle this new discovery properly
      self.root.modified = True
      saveGame(self.root)

    return val
  def confirmPrompt(self, original: "Game", question: str) -> bool:
    question += " [y]/n:"
    rsp = self.requestVal(original, question, printState=False, disableAutoSave=True, printOptions=False)
    return (rsp or "y").strip()[0].lower()
  def requestVal(self, original: "Game", request: str, printState=True, disableAutoSave=False, printOptions=True) -> str:
    if printState:
      original.printVials()
      original.printMoves()

    # Other options start with a dash
    if printOptions: print("Other options:\n" +
          "   -o VIAL SPACE COLOR     to provide other values\n" +
          "   -p or -print            to print the ROOT board\n" +
          "   -pc                     to print the CURRENT board\n" +
          "   -c or -colors           to print the distribution of colors in the vials\n" +
          "   -s or -save             to save the discovered colors\n" +
          "   -r or -reset            to reset the search algorithm\n" +
          "   -m OR -moves            to print the moves to this point\n" +
         f"   -solve METHOD           to change the solve method ({', '.join(VALID_SOLVE_METHODS)})\n" +
          "   -level NUM              to change the level of this game\n" +
          "   -vials NUM              to change the number of vials in the game\n" +
          "   -e OR -exit             to save and exit\n" +
          "   -q OR quit              to quit\n" +
          "   -d OR -debug            to see debug info")
    rsp: str
    while True:
      optionPrompt = "(Or see other options above.)" if printOptions else "(Or use advanced options.)"
      print(request + " " + optionPrompt)

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
          Game.latest = None
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
        elif rsp.startswith("-solve"):
          setSolveMethod(rsp.split(" ")[1])
          Game.reset = True
          return ""
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

    if not disableAutoSave: saveGame(self.root)
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

  def _identifyUnderusedColors(self, colorDist: dict[str, int]) -> list[str]:
    return [color for color, count in colorDist.items() if count < NUM_SPACES_PER_VIAL and color != "?"]
  def _findFirstSpaceWithColor(self, color: str) -> tuple[int, int]:
    """
    Returns the vial index and space index of the first occurrence of a particular color.
    """
    return next(((vialIndex, spaceIndex) for vialIndex, vial in enumerate(self.vials) for spaceIndex, val in enumerate(vial) if val == color), None)

  MoveInfo = tuple[str, int, bool, bool, bool]
  """ (colorMoved, numMoved, isComplete, vacatedVial, startedVial) OR None """

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
        info = curGame.__getMoveInfo()
        moveString = formatVialColor(info[0], f"{start+1}->{end+1}", ljust=8)
        lines.appendleft(moveString + curGame.__getMoveString(info))
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

    color: str = None
    for spaceIndex in range(NUM_SPACES_PER_VIAL):
      for vialIndex in range(self.__numVials):
        color = self.vials[vialIndex][spaceIndex]
        lines[spaceIndex + 1].append("\t" + formatVialColor(color, text=color))

    print("\n".join(["".join(line) for line in lines]))
  def __getMoveString(self, info: MoveInfo = None) -> str:

    if not info:
      info = self.__getMoveInfo()
    result: str
    if info == None:
      result = ""
    else:
      color, num, complete, vacated, startedVial = info
      extraStr = ""
      if complete:
        extraStr = Game.COMPLETE_STR
      elif vacated:
        extraStr = Game.VACATED_STR
      elif startedVial:
        extraStr = Game.STARTED_STR
      numStr = Style.BRIGHT + str(num) + Style.NORMAL if num > 1 else num
      result = f"({numStr} {color}{extraStr})"

    return result.ljust(Game.TOTAL_MOVE_PRINT_WIDTH)
  def __getMoveInfo(self) -> MoveInfo:
    if not self.move:
      return None
    start, end = self.move

    colorMoved = self.getTopVialColor(end)
    _, _, numMoved, startEmptySpaces   = self.prev.__countOnTop(colorMoved, start)
    complete, _, _, endEmptySpaces     = self.__countOnTop(colorMoved, end)

    vacatedVial = numMoved + startEmptySpaces == NUM_SPACES_PER_VIAL
    startedVial = NUM_SPACES_PER_VIAL - numMoved == endEmptySpaces
    return (colorMoved, numMoved, complete, vacatedVial, startedVial)
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
      lines.append(f"  {formatVialColor(color, text=color)}: \t{count}" + label)

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

    # Track the completion order
    if willComplete:
      self.__registerCompletion(endColor)

    # Finish
    return True
  def __registerCompletion(self, completingColor: str) -> None:
    newCompletions = self.completionOrder.copy()
    newCompletions.append((completingColor, self._numMoves))
    self.completionOrder = newCompletions

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

    if self.move:
      # TODO: this only evaluates the most recent move,
      # but the algorithm could have inserted another move in between.
      # More generically, we need to ensure that we never make a move from
      # a vial, if the vial it would move into hasn't changed since the
      # starting vial was filled. (That's a lot more complicated.)
      moveValid[self.move[1]] = False

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
    return " ".join(out)
  def __eq__(self, other: object) -> bool:
    """Overrides the default implementation"""
    if isinstance(other, Game):
      return self.__str__() == other.__str__()
    return False
  def __hash__(self) -> int:
    return hash(self.__str__())

  def _getCompletionStr(self) -> str:
    return " ".join(map(lambda x: x[0], self.completionOrder))
  def _completion_eq(self, other: object) -> bool:
    if isinstance(other, Game):
      return self._getCompletionStr() == other._getCompletionStr()
    return False
  def _completion_hash(self) -> int:
    return hash(self._getCompletionStr())

  def getNumVials(self) -> int:
    return self.__numVials
  def getDepth(self) -> int:
    return self._numMoves

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
    searchBFS: bool = False
    if Game.latest:
      q.append(Game.latest)
      Game.latest = None
      searchBFS = True
    else:
      q.append(game)
      searchBFS = shouldSearchBFS()

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
      if not searchBFS and minSolution and minSolution._numMoves <= current._numMoves:
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
  """
  Reads the game one line at a time by invoking a configurable `nextLine()` method.

  Users are presented with nice prompts asking for each piece of information.
  With users, the number of vials is determined based on when an empty line is parsed.

  When reading from files, the prompts are suppressed and the number of vials is
  explicitly read as the first line of input.
  """
  numVials = -1
  if not userInteraction:
    rsp = nextLine()  # Read num vials from input file
    numVials = int(rsp)

  vials = []

  # Automatically detect the last empty vials
  numEmpty = 0
  if userInteraction:
    numEmpty = _determineNumEmpty(numVials)

  # Read in the colors
  if userInteraction: print(f"On the next lines, please type {NUM_SPACES_PER_VIAL} words representing the colors in each vial from top to bottom.\n"+
                            "  Stopping short of the depth of a vial will fill the remaining spaces with question marks.\n" +
                            "  Type a . (period) to insert a whole row of question marks.\n" +
                            "  Type a blank line signal that all vials with colors have been represented (all remaining vials are empty).\n")
  emptyRest = False
  i = 0
  while i < numVials or numVials == -1:
    i += 1
    if numVials != -1 and (emptyRest or i > numVials - numEmpty):
      vials.append(["-"] * NUM_SPACES_PER_VIAL)
      continue

    if userInteraction: print(f"Vial {i}: ")
    response = nextLine()
    if response == "" or not response:
      emptyRest = True
      i -= 1 # Place an empty value for this row
      if userInteraction:
        numVials = len(vials)
        numVials += _determineNumEmpty(numVials)
      continue

    if response == ".":
      vials.append(["?"] * NUM_SPACES_PER_VIAL)
      continue

    spaces = response.split()
    while len(spaces) < NUM_SPACES_PER_VIAL:
      spaces.append("?")
    vials.append(spaces)

  return Game.Create(vials)
def _determineNumEmpty(vialsWithColors: int) -> int:
  return 1 if vialsWithColors < FEW_VIALS_THRESHOLD else 2

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
    playGame(originalGame)
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

def saveGame(game: "Game", forceSave = False) -> None:
  if not game or (not forceSave and not game.modified):
    return None # No saving necessary
  fileName = generateFileName(game.level)
  result = generateFileContents(game)
  saveFileContents(fileName, result)
  game.modified = False
  print(f"Saved discovered game state to file: {fileName}")
def getBasePath(absolutePath = WRITE_FILES_TO_ABSOLUTE_PATH) -> str:
  return INSTALLED_BASE_PATH if absolutePath else ""
def generateFileName(levelNum: str, absolutePath: bool = None) -> str:
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

def autoSwitchForUnknownsApply(newState="MIX") -> None:
  return _autoSwitchForUnknowns(True, newState)
def autoSwitchForUnknownsRevert() -> None:
  return _autoSwitchForUnknowns(False)
def _autoSwitchForUnknowns(applyState: bool, newState="MIX") -> None:
  global AUTO_BFS_FOR_UNKNOWNS_ORIG_METHOD

  if applyState:
    AUTO_BFS_FOR_UNKNOWNS_ORIG_METHOD = SOLVE_METHOD
    setSolveMethod(newState)
  else:
    setSolveMethod(AUTO_BFS_FOR_UNKNOWNS_ORIG_METHOD)
    AUTO_BFS_FOR_UNKNOWNS_ORIG_METHOD = None
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

def generateAnalysisResultsName(level: str, absolutePath: bool = None) -> str:
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

def formatVialColor(color: str, text: str = "", ljust=0) -> str:
  """Formats a color for printing. If text is provided, it will autoreset the style afterwards as well."""
  out = COLOR_CODES[color]
  if text:
    out += text + Style.RESET_ALL
    out += " " * (ljust - len(text))
  return out

def formatSpaceRef(vialIndex: int, spaceIndex: int) -> str:
  return f"{vialIndex+1}:{spaceIndex+1}"

GLOBAL_GAME_IN_PROGRESS: Game | None = None
def signalHandler(signum, frame):
  print(f" Emergency quitting for signal ({signal.strsignal(signum)})")
  saveGame(GLOBAL_GAME_IN_PROGRESS)
  exit(0)
signal.signal(signal.SIGINT, signalHandler)

# Run the program!
# Call signatures:
# py watersort.py LEVEL a SAMPLES?
# py watersort.py a LEVEL SAMPLES?
# py watersort.py LEVEL <MODE>
# py watersort.py LEVEL dfr SAMPLES?
chooseInteraction()
