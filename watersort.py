import copy
import itertools
import os
import random
import signal
import sys
import threading
from collections import deque, defaultdict
from colorama import Fore
from dataclasses import dataclass
from datetime import datetime
from math import floor, log, ceil
from resources import COLOR_CODES, COLOR_FOREGROUND, COLOR_NAMES, MONTH_ABBRS, RESERVED_COLORS, BigChar, BigShades, Style
from time import time
from typing import Callable, Literal

USE_READCHAR = True
if USE_READCHAR:
  from readchar import readkey, key

INSTALLED_BASE_PATH = ""
WRITE_FILES_TO_ABSOLUTE_PATH = False

SOLVER_VERSION = 3
ANALYZER_VERSION = 6

NUM_SPACES_PER_VIAL = 4
DEBUG_ONLY = False
FORCE_SOLVE_LEVEL = None # "263"
FORCE_INTERACTION_MODE = None # "a"


SOLVE_METHOD = "DFR"
VALID_SOLVE_METHODS = set(["MIX", "BFS", "DFS", "DFR"]) # An enum is more accurate, but overkill for this need
VALID_GAMEPLAY_MODES = set(["drain", "blind"])

MIX_SWITCH_THRESHOLD_MOVES = 10
ENABLE_QUEUE_CHECKS = True # Disable only for temporary testing

SHUFFLE_NEXT_MOVES = False
ANALYZE_ATTEMPTS = 10000
DFR_SEARCH_ATTEMPTS = 200

CONFIRM_APPLY_LAST_UNKNOWN = False
CONFIRM_APPLY_LAST_BATCH_COLOR = False
AUTO_BFS_FOR_UNKNOWNS_ORIG_METHOD = None

FEW_VIALS_THRESHOLD = 7 # I'm not actually sure if this is the right threshold, but it appears correct

Vials = list[list[str]]
Move = tuple[int, int]
""" (startVialIndex, endVialIndex) """

@dataclass(frozen=True)
class DeadEndSearchResults:
  game: "Game"
  searchIterations: int
  searchSeconds: float
  numDeadEnds: int
  numEventualSolutions: int

  searchDataAvailable: bool = True

  @property
  def hasDeadEnds(self):
    return self.numDeadEnds>0


class SolutionStep:
  game: "Game"
  move: Move

  # For special steps
  bigText: str|None

  # Fields received from MoveInfo
  info: "Game.MoveInfo"
  colorMoved: str
  numMoved: int
  isComplete: bool
  vacatedVial: bool
  startedVial: bool

  # Comparison to previously reported solution
  isSameAsPrevious: bool|None

  # Pre-compute stat values
  deadEndsSearch: DeadEndSearchResults|None = None

  def __init__(self, game: "Game"=None, info: "Game.MoveInfo"=None, bigText: str = None):
    self.bigText = bigText

    self.game = game
    self.move = game.move if game else None

    if info is None and game is not None:
      info = game.getMoveInfo()

    if info:
      self.info = info
      self.colorMoved = info[0]
      self.numMoved = info[1]
      self.isComplete = info[2]
      self.vacatedVial = info[3]
      self.startedVial = info[4]
    else:
      self.info = None
      self.colorMoved = None
      self.numMoved = 0
      self.isComplete = False
      self.vacatedVial = False
      self.startedVial = False

    self.isSameAsPrevious = None

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
  # TODO: Move these static fields to the Solver class instead
  reset: bool = False
  quit: bool = False
  latest: "Game" = None
  preferBigMoves: bool = True

  # Flags set on the root game
  level: str
  modified: bool # Indicates it's changed from the last read in state
  _colorError: bool
  _hasUnknowns: bool
  drainMode: bool = None
  """Special mode where colors drain out of the bottom of vials instead of pouring from the top."""
  blindMode: bool = None
  """Represents FULL-blind mode where spaces re-hide themselves after moving."""
  hadMysterySpaces: bool = False
  """Automatically flagged when mystery tiles are discovered."""

  @property
  def specialModes(self) -> list[str]:
    modes = []
    if self.root.drainMode:
      modes.append("drain")
    if self.root.blindMode:
      modes.append("blind")
    if self.root.hadMysterySpaces:
      modes.append("mystery")
    return modes

  # Cached for single use calculation
  _COMPLETE_TERM = "complete"
  _VACATED_TERM = "vacated"
  _STARTED_TERM = "occupied"
  COMPLETE_STR = Style.BRIGHT + _COMPLETE_TERM + Style.NORMAL
  VACATED_STR = Style.DIM + _VACATED_TERM + Style.NORMAL
  STARTED_STR = Style.DIM + _STARTED_TERM + Style.NORMAL
  COLOR_WIDTH = 3             # CONSIDER: Make more direct by dynamically figuring the maximum color length
  NUMBER_WIDTH = 1            # Num is always less than NUM_SPACES_PER_VIAL (which is small)
  EXTRA_CHARS = 4             # The number of additional chars in our result string
  TOTAL_MOVE_PRINT_WIDTH = COLOR_WIDTH + NUMBER_WIDTH + EXTRA_CHARS + len(COMPLETE_STR)

  @staticmethod
  def Create(vials, drainMode=False, blindMode=False) -> "Game":
    newGame = Game(vials, None, None)
    newGame.drainMode = bool(drainMode)
    newGame.blindMode = bool(blindMode)
    newGame._analyzeColors()
    return newGame

  def __init__(self, vials: "Vials", move: "Move", prev: "Game", modified = False):
    self.vials = copy.deepcopy(vials)
    self.__numVials = len(vials)
    self.move = move
    self.prev = prev
    self.modified = modified

    self.__isRoot = prev is None
    self.root = self if self.__isRoot else prev.root
    self._numMoves = 0 if self.__isRoot else prev._numMoves + 1
    self.completionOrder = list() if self.__isRoot else prev.completionOrder

  def getNthParent(self, n: int) -> "Game":
    """Returns the nth-parent of the game, or None if n is greater than the number of parents."""
    out = self
    for _ in range(n):
      if out.prev:
        out = out.prev
      else:
        return None
    return out
  def hasError(self) -> bool:
    return self._colorError # Or other errors
  def attemptCorrectErrors(self) -> bool:
    """Attempts to correct any errors, and then returns a bool indicating if errors still exist"""
    if not self.hasError():
      return False

    self.requestVal(formatVialColor("er", "The colors aren't right in this game.") + " Fix them, and press enter to proceed.")
    self._analyzeColors()
    if self.hasError():
      saveGame(self, forceSave=True)
      print(formatVialColor("er", "Things still aren't right.") + " Review the saved file, and try again.")
      quit()
      return True
    else:
      print("Issues resolved. Proceeding.")
      return False

  def getTopVialColor(self, vialIndex, bottom = False) -> str:
    vial = self.vials[vialIndex]
    iterator = range(NUM_SPACES_PER_VIAL)
    if bottom: iterator = reversed(iterator)
    for i in iterator:
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

    rootVal = self.tryAccessVal(vialIndex, spaceIndex)
    return rootVal or "?"
  def tryAccessVal(self, vialIndex, spaceIndex) -> str:
    root = self.root
    val = root.vials[vialIndex][spaceIndex]
    if val != "?":
      return val

    if not root.hadMysterySpaces:
      root.hadMysterySpaces = True
      root.modified = True
      # Allow this change to be picked up by the next save cycle

    print("\n\n", end="")
    if SOLVE_METHOD == "DFR":
      resolveWithMethod = "MIX"
      print(f"Unknown value detected with {SOLVE_METHOD} solve method. Re-solving with {resolveWithMethod} to detect unknown values.")
      autoSwitchForUnknownsApply(newState=resolveWithMethod)
      Game.reset = True
      return None # No value requested

    print("Discovering new value:")
    startVial = vialIndex + 1
    request = f"What's the new value in the {startVial} vial, {spaceIndex+1} space?"
    colorDist, colorErrors = root._analyzeColors()
    if colorDist["?"] > 0:
      underusedColors = sorted(Game._identifyUnderusedColors(colorDist))
      fewColors = [formatVialColor(color, color) for color in underusedColors]
      request += f" ({colorDist['?']} remaining unknowns: {', '.join(fewColors)})"

    rootChanged = False

    repromptCount = -1
    while True:
      repromptCount += 1
      val = self.requestVal(request, printState=repromptCount==0, printOptions=None if repromptCount == 0 else False)
      if val:
        rootChanged = True
        Game.latest = self
        spaces = val.strip().split()
        if spaceIndex + len(spaces) > NUM_SPACES_PER_VIAL:
          print(formatVialColor("er", "Too many colors.") + f" Multiple colors can be entered, but the total number of spaces cannot exceed {NUM_SPACES_PER_VIAL}.")
          continue # Reprompt the user
        root.vials[vialIndex][spaceIndex:spaceIndex+len(spaces)] = spaces
        self.vials[vialIndex][spaceIndex:spaceIndex+len(spaces)] = spaces
      break

    colorDist, colorErrors = root._analyzeColors()
    underusedColors = Game._identifyUnderusedColors(colorDist)

    if colorDist["?"] == 1:
      lastColor = next((k for k, v in colorDist.items() if (v < NUM_SPACES_PER_VIAL and k != "?")), None)
      lastVialIndex, lastVialSpace = root._findFirstSpaceWithColor("?")
      lastSpace = formatSpaceRef(lastVialIndex, lastVialSpace)

      request =   "There is only one remaining unknown value."

      proceed = True
      if CONFIRM_APPLY_LAST_UNKNOWN:
        request += f" Would you like to save {formatVialColor(lastColor, lastColor)} into space {lastSpace}?"
        proceed = self.confirmPrompt(request)
      else:
        request += f" Saving color {formatVialColor(lastColor, lastColor)} into space {lastSpace}."
        print(request)

      if proceed:
        root.vials[lastVialIndex][lastVialSpace] = lastColor
        self.vials[lastVialIndex][lastVialSpace] = lastColor
        rootChanged = True
    elif colorDist["?"] <= NUM_SPACES_PER_VIAL and len(underusedColors) == 1:
      lastColor = underusedColors[0]
      request = "Only one potential color remains to fill the unknowns."

      proceed = True
      if CONFIRM_APPLY_LAST_BATCH_COLOR:
        request += f" Would you like to save {formatVialColor(lastColor, lastColor)} in *all* {colorDist['?']} spaces?"
        proceed = self.confirmPrompt(request)
      else:
        request += f" Saving color {formatVialColor(lastColor, lastColor)} into {colorDist['?']} remaining spaces."
        print(request)

      if proceed:
        Game.latest = None
        for vialIdx, spaceIdx in itertools.product(range(self.__numVials), range(NUM_SPACES_PER_VIAL)):
          if root.vials[vialIdx][spaceIdx] == "?":
            root.vials[vialIdx][spaceIdx] = lastColor
            self.vials[vialIdx][spaceIdx] = lastColor


    if rootChanged:
      Game.reset = True # Reset the search to handle this new discovery properly
      root.modified = True
      saveGame(root)

    colorDist, colorErrors = root._analyzeColors()
    if colorDist["?"] == 0 and AUTO_BFS_FOR_UNKNOWNS_ORIG_METHOD:
      doResolveLevel = True
      if Game.latest:
        prompt = Style.BRIGHT + "All unknowns located." + Style.NORMAL + " Would you like to re-solve to find the shortest solution?"
        defaultYes = self._numMoves < 10
        doResolveLevel = self.confirmPrompt(prompt, defaultYes=defaultYes)

      if doResolveLevel:
        print("Reverting to original solve method now that all discovered values are found.")
        autoSwitchForUnknownsRevert()
        Game.reset = True
        Game.latest = None
      else:
        Game.reset = False
        SolutionSolver.MysteryContinuation = True

    saveGame(root)
    return val
  def confirmPrompt(self, question: str, defaultYes=True) -> bool:
    question += " [y]/n:" if defaultYes else " y/[n]:"
    rsp = self.requestVal(question, printState=False, disableAutoSave=True, printOptions=False)
    if not rsp: return defaultYes
    return rsp.strip()[0].lower() == "y"
  def requestVal(self, request: str, printState=True, disableAutoSave=False, printOptions:bool=None) -> str:
    if printState:
      if Game.preferBigMoves and self.move:
        BigSolutionDisplay(self).start()
      else:
        self.printVials()
        self.printMoves()

    # Other options start with a dash
    if printOptions != False:
      self.__requestValHelp(abbreviated=(printOptions is None))
    rsp: str
    while True:
      optionPrompt = "(Or see other options above.)" if printOptions else "(Or use advanced options.)"
      print(request + " " + optionPrompt)

      rsp = input()
      if not rsp:
        # CONSIDER: This may not actually be the best behavior
        break
      elif rsp == "quit" or rsp[0] == "-":
        action = self._handleSpecialOption(rsp)
        if action is not None:
          return action
      else:
        # They answered the original question
        break

    if not disableAutoSave: saveGame(self.root)
    return rsp
  def _handleSpecialOption(self, rsp: str):
    """
    Interprets and acts on a special command represented as a string.
    The commands available are described by the helptext, and with one exception, they begin with a hyphen (-).

    @returns None when no action is required, otherwise a value with which to immediately return as if entered as a normal value
    """
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
    elif rsp == "-h" or rsp == "-help":
      self.__requestValHelp()
    elif rsp == "-p" or rsp == "-print":
      root.printVials()
    elif rsp == "-pc":
      self.printVials()
    elif rsp == "-m" or rsp == "-moves":
      self.printMoves()
    elif rsp == "-b":
      BigSolutionDisplay(self).start()
    elif rsp == "-d" or rsp == "-debug":
      print("Printing debug info... (None)")
      # TODO: Print the queue length, and other search related stats
    elif rsp == "-c" or rsp == "-colors" or rsp == "-color":
      root.printColors()

    # Special commands
    elif rsp.startswith("-b "):
      self.saveNewBigMovesSetting(rsp, self)
    elif rsp.startswith("-solve"):
      setSolveMethod(rsp.split(" ")[1])
      Game.reset = True
      return ""  # Immediately return to re-solve
    elif rsp.startswith("-gameplay"):
      self.saveNewGameplayMode(rsp)
    elif rsp.startswith("-level"):
      self.saveNewLevel(rsp)
    elif rsp.startswith("-o"):
      self.saveOtherColor(rsp)
    elif rsp.startswith("-v"):
      self.saveNewVials(rsp)

    # Default
    else:
      print("Unrecognized command: " + rsp)

    return None
  def __requestValHelp(self, abbreviated = False) -> None:
    if abbreviated:
      print("Other options (basic):\n" +
            "   -h or -help             to view detailed help screen\n" +
            "   -o VIAL SPACE COLOR     to provide other values\n" +
            "   -b                      to view Big Moves up to this point\n" +
            "   -e or -exit             to save and exit")
    else:
      print("Other options (advanced):\n" +
            "   -h or -help             to view this help screen\n" +
            "   -o VIAL SPACE COLOR     to provide other values\n" +
            "   -p or -print            to print the ROOT board\n" +
            "   -pc                     to print the CURRENT board\n" +
            "   -c or -colors           to print the distribution of colors in the vials\n" +
            "   -s or -save             to save the discovered colors\n" +
            "   -r or -reset            to reset the search algorithm\n" +
            "   -m or -moves            to print the moves to this point\n" +
            "   -b                      to view Big Moves up to this point\n" +
            "   -b on|off|ON            Enable/disable Big Moves by default. Specify ON (all-caps) to skip launching routine.\n" +
           f"   -gameplay MODE          to toggle other forms of gameplay ({', '.join(VALID_GAMEPLAY_MODES)})\n" +
           f"   -solve METHOD           to change the solve method ({', '.join(VALID_SOLVE_METHODS)})\n" +
            "   -level NUM              to change the level of this game\n" +
            "   -vials NUM              to change the number of vials in the game\n" +
            "   -e or -exit             to save and exit\n" +
            "   -q or quit              to quit\n" +
            "   -d or -debug            to see debug info")
  def saveNewBigMovesSetting(self, input: str) -> None:
    setting = input.split()[1]
    settingLower = setting.lower()

    if settingLower == "on":
      Game.preferBigMoves = True
      print("Big Moves enabled by default.")
      if setting != "ON":
        BigSolutionDisplay(self).start()
    elif settingLower == "off":
      Game.preferBigMoves = False
      print("Big Moves disabled by default.")
    else:
      print(f"Unrecognized option for -b: {setting}")
  def saveNewGameplayMode(self, input: str) -> None:
    flag, mode = input.split()
    mode = mode.strip().lower()
    if mode not in VALID_GAMEPLAY_MODES:
      print(f"Unrecognized gameplay mode: {mode}. Valid modes are: {', '.join(VALID_GAMEPLAY_MODES)}")
      return

    newVal: bool = None
    if mode == "drain":
      newVal = self.root.drainMode = not self.root.drainMode
    elif mode == "blind":
      newVal = self.root.blindMode = not self.root.blindMode

    Game.reset = True
    self.root.modified = True
    print(f"Gameplay mode '{mode}' {'enabled' if newVal else 'disabled'}. Resetting to resolve.")
  def saveOtherColor(self, input: str) -> None:
    flag, o_vial, o_space, color = input.split()
    vial = int(o_vial) - 1 # Assumes a valid integer
    space = int(o_space) - 1 # Assumes a valid integer
    Game.reset = True
    self.root.modified = True
    self.root.vials[vial][space] = color
    self.vials[vial][space] = color
    print(f"Saved color '{color}' to vial {o_vial} in slot {o_space}. Continue on.")
  def saveNewLevel(self, input: str) -> None:
    flag, o_level = input.split()
    self.level = o_level
    self.root.level = o_level
    self.root.modified = True
    print(f"Saved new level ({o_level}). Continue on.")
  def saveNewVials(self, input: str) -> None:
    flag, o_vials = input.split()
    numVials = int(o_vials) # Assumes a valid integer

    target = self.root
    if numVials > len(target.vials):
      target.modified = True
      Game.reset = True
      while numVials > len(target.vials):
        target.vials.append(["-"] * NUM_SPACES_PER_VIAL)
      print(f"Increased number of vials to {numVials}")
    elif numVials < len(target.vials):
      target.modified = True
      Game.reset = True
      target.vials = target.vials[0:numVials]
      print(f"Truncated the vials to only the first {numVials}")
    else:
      print(f"No change to number of vials. Still have {numVials}")
    target.__numVials = numVials
  @staticmethod
  def _identifyUnderusedColors(colorDist: dict[str, int]) -> list[str]:
    return [color for color, count in colorDist.items() if count < NUM_SPACES_PER_VIAL and color != "?"]
  def _findFirstSpaceWithColor(self, color: str) -> tuple[int, int]:
    """
    Returns the vial index and space index of the first occurrence of a particular color.
    """
    return next(((vialIndex, spaceIndex) for vialIndex, vial in enumerate(self.vials) for spaceIndex, val in enumerate(vial) if val == color), None)

  MoveInfo = tuple[str, int, bool, bool, bool]
  """ (colorMoved, numMoved, isComplete, vacatedVial, startedVial) OR None """

  def printMoves(self, fromGame: "Game" = None) -> None:
    """Prints out the moves taken to reach this game state."""
    steps: deque[SolutionStep] = self._prepareSolutionSteps(fromGame)

    NEW_LINE = "\n  "
    SEPARATOR = "\t "

    lines = []
    if not steps:
      lines.append("None")
    else:
      for step in steps:
        moveString = self.getMoveString(step)
        if step.isSameAsPrevious != None:
          moveString += SEPARATOR + ("(same)" if step.isSameAsPrevious else "(different)")
        lines.append(moveString)

    introduction = f"Moves ({len(steps)})"
    if self.root.drainMode:
      introduction += " [Drain Gameplay]"
    print(introduction + ":" + NEW_LINE + NEW_LINE.join(lines))

  __prevPrintedMoves: deque[Move] = None
  def _prepareSolutionSteps(self, fromGame: "Game" = None) -> deque[SolutionStep]:
    """Prepares the solution steps to be printed, including comparison to previous printed solution."""
    steps = deque()
    if not self.move:
      Game.__prevPrintedMoves = None
      return steps

    # Collect moves
    curGame = self
    moves = deque()
    while curGame and curGame.move:
      if curGame == fromGame:
        return steps # Skip comparison against previous prints

      moves.appendleft(curGame.move)
      steps.appendleft(SolutionStep(curGame))
      curGame = curGame.prev

    # Compare to previous printed moves
    if Game.__prevPrintedMoves:
      prevMoves = Game.__prevPrintedMoves
      i = 0
      while i < len(prevMoves) and i < len(moves):
        if moves[i] == prevMoves[i]:
          steps[i].isSameAsPrevious = True
        else:
          steps[i].isSameAsPrevious = False
          break  # All subsequent moves are different
        i += 1

    Game.__prevPrintedMoves = moves
    return steps

  def getMoveString(self, step: SolutionStep) -> str:
    """Returns a string with a fixed justification, including escape character for formatting, that describes the move."""
    start, end = step.move
    result = formatVialColor(step.colorMoved, f"{start+1}->{end+1}", ljust=8)
    result += self._getMoveInfoString(step.info)
    return result
  def _getMoveInfoString(self, info: MoveInfo = None) -> str:
    if not info:
      info = self.getMoveInfo()

    result: str
    if info is None:
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
      if extraStr: extraStr = " " + extraStr
      result = f"({numStr} {color}{extraStr})"

    return result.ljust(Game.TOTAL_MOVE_PRINT_WIDTH)
  def getMoveInfo(self) -> MoveInfo:
    if not self.move:
      return None
    start, end = self.move

    colorMoved = self.getTopVialColor(end)
    _, _, numMoved, startEmptySpaces   = self.prev.__countOnTop(colorMoved, start, bottom=self.root.drainMode)
    complete, _, _, endEmptySpaces     = self.__countOnTop(colorMoved, end)

    vacatedVial = numMoved + startEmptySpaces == NUM_SPACES_PER_VIAL
    startedVial = NUM_SPACES_PER_VIAL - numMoved == endEmptySpaces
    return (colorMoved, numMoved, complete, vacatedVial, startedVial)
  def printVials(self, numberSpaces=False) -> None:
    lines = [list() for _ in range(NUM_SPACES_PER_VIAL + 1)]

    if numberSpaces:
      for lineIndex in range(NUM_SPACES_PER_VIAL + 1):
        lines[lineIndex].append(" " if lineIndex==0 else str(lineIndex))

    for i in range(self.__numVials):
      lines[0].append("\t" + str(i + 1))

    color: str = None
    for spaceIndex in range(NUM_SPACES_PER_VIAL):
      for vialIndex in range(self.__numVials):
        color = self.vials[vialIndex][spaceIndex]
        lines[spaceIndex + 1].append("\t" + formatVialColor(color, text=color))

    print("\n".join(["".join(line) for line in lines]))

  def printColors(self, analyzedData = None) -> list[str]:
    """Prints out the state of the colors, including any errors"""
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
    if not self.root.drainMode and self.move and startVial == self.move[1] and endVial == self.move[0]:
      return INVALID_MOVE # Can't simply undo the previous move

    startColor = self.getTopVialColor(startVial, bottom=self.root.drainMode)
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
    startIsComplete, startOnlyColor, startNumOnTop, startEmptySpaces = self.__countOnTop(startColor, startVial, bottom=self.root.drainMode)
    if startIsComplete:
      return INVALID_MOVE # Start is fully filled
    if startNumOnTop > endEmptySpaces:
      # CONSIDER: This may not actually be an invalid move
      return INVALID_MOVE # Only pour when it can all be received
    if endColor == "-" and (startOnlyColor or self.__findSoloVial(startColor, skipVial=startVial) is not None):
      return INVALID_MOVE # Never occupy a new container when we already have one

    # Compute additional fields
    willComplete = endOnlyColor and startNumOnTop == endEmptySpaces
    compareVialFillLevel = False

    # When completing a vial, never move more spaces than necessary
    if startOnlyColor and endOnlyColor:
      compareVialFillLevel = True
    # When vacating a vial, always prefer to move into an existing "only" vial
    elif startOnlyColor:
      otherSoloVial = self.__findSoloVial(startColor, skipVial=startVial)
      if otherSoloVial is not None and endVial != otherSoloVial:
        return INVALID_MOVE # We should not be vacating a vial if we could be combining with another solo vial instead
      compareVialFillLevel = True

    # Avoid moving a large number of squares onto a small number of squares
    # Break ties by preferring vials towards the end of the list
    if compareVialFillLevel:
      startCompVal = startNumOnTop + (startVial / 1000)
      endCompVal = endNumOnTop + (endVial / 1000)
      if startCompVal > endCompVal:
        return INVALID_MOVE

    # It's valid
    return (True, startColor, endColor, endEmptySpaces, willComplete)
  # topColor SHOULD NOT be "-" or "?"
  def __countOnTop(self, topColor: str, vialIndex: int, bottom=False) -> tuple[bool, bool, int, int]: # (isComplete, isOnlyColorInColumn, numOfColorOnTop, numEmptySpaces)
    isComplete = True
    onlyColor = True
    emptySpaces = 0
    numOnTop = 0

    vial = self.vials[vialIndex]
    emptySpaceVal = 1 # We only want to count empty spaces that appear BEFORE colors

    iterator=range(NUM_SPACES_PER_VIAL)
    if bottom: iterator=reversed(iterator)
    for i in iterator:
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
  def __findSoloVial(self, forColor: str, skipVial=None) -> int | None:
    """Locates a vial that contains *only* the specified color. If no vial exists, returns None."""
    for searchVial in range(len(self.vials)):
      if searchVial == skipVial: continue
      _, isOnlyColor, numOnTop, _ = self.__countOnTop(forColor, searchVial)
      if isOnlyColor and numOnTop > 0:
        return searchVial
    return None

  def makeMove(self, startVial, endVial) -> bool:
    valid, startColor, endColor, endSpaces, willComplete = self.__prepareMove(startVial, endVial)
    if not valid:
      return False

    fromVial = self.vials[startVial]
    toVial = self.vials[endVial]

    # Remove up to that many colors from start
    piecesMoved = 0
    moveRange = endSpaces
    startColors = 0
    while piecesMoved < moveRange and piecesMoved < NUM_SPACES_PER_VIAL:
      idx = NUM_SPACES_PER_VIAL-piecesMoved-1 if self.root.drainMode else piecesMoved
      color = fromVial[idx]
      if color == '-':
        moveRange += 1
      elif color == startColor:
        startColors += 1
        fromVial[idx] = "-"
      else:
        break
      piecesMoved += 1

    # Shift down moved colors in drain mode
    if self.root.drainMode:
      for i in range(NUM_SPACES_PER_VIAL-1,-1,-1):
        shiftFrom = i - piecesMoved
        shiftColor = "-" if shiftFrom < 0 else fromVial[shiftFrom]
        fromVial[i] = shiftColor

    # Add the values back to endVial, from the bottom
    i = NUM_SPACES_PER_VIAL - 1
    moveRange = startColors
    while i >= 0 and moveRange > 0:
      color = toVial[i]
      if color == '-':
        moveRange -= 1
        toVial[i] = startColor
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
    newGame = Game(self.vials, move, self)
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

class BigSolutionDisplay:
  rootGame: "Game"
  targetGame: "Game"
  movesFinishGame: bool
  _presteps: deque[SolutionStep]
  _steps: deque[SolutionStep]
  _poststeps: deque[SolutionStep]

  __currentPrestep: int
  __currentStep: int
  __currentPoststep: int

  _currentStage: Literal["PRE","GAME","POST"]
  """ Pre -> Game -> Post. Can advance back from POST, but can never return to PRE. """
  _currentSpacesMoved: int
  """The number of spaces that will have been moved after the user completes the indicated action."""

  SCREEN_WIDTH = 80
  SCREEN_HEIGHT = 20

  detailInformation = False
  debugInformation = False

  _maxDeadEnds: DeadEndSearchResults|None
  _earliestSafeStep: DeadEndSearchResults|None
  __simpleDeadEndsMax = 99
  __spawnThreadLock = threading.Lock()
  __hasSpawnedThread = False
  """This critical, shared source indicates if we have a lock. Only access this variable while holding __spawnThreadLock!"""
  __finishedDeadEndsSearch: bool
  """Indicates if there is still potential for the worker thread to compute more states."""
  __lastComputedDeadEndStepDepth: int|None

  @staticmethod
  def __updateScreenWidth() -> None:
    termSize = os.get_terminal_size()
    BigSolutionDisplay.SCREEN_WIDTH = termSize.columns
    BigSolutionDisplay.SCREEN_HEIGHT = termSize.lines

  def __init__(self, game: Game):
    self.rootGame = game.root
    self.targetGame = game

    self._presteps = deque()
    self._steps = game._prepareSolutionSteps()
    self._poststeps = deque()


    self.__currentPrestep = 0
    self.__currentStep = 0
    self.__currentPoststep = 0
    self._currentStage = "GAME"
    self._currentSpacesMoved = 0

    self._maxDeadEnds = None
    self._earliestSafeStep = None
    self.__finishedDeadEndsSearch = False
    self.__lastComputedDeadEndStepDepth = None

    if self._steps:
      self.movesFinishGame = self._steps[-1].game.isFinished()
      self.__init_presteps()
      self.__init_poststeps()
      self._launchDeadEndComputationBackground()

    BigSolutionDisplay.__updateScreenWidth()
  def __init_presteps(self):
    if self._steps[0].isSameAsPrevious is None:
      return # No comparison to a previous print sequence

    # Determine text to display
    bigText: str = None
    firstNewIndex, firstNewStep = next(((i, s) for i, s in enumerate(self._steps) if s.isSameAsPrevious is not True), (None, None))
    if firstNewStep is None:
      bigText = "REPEAT"  # Expected to be unused
    elif firstNewStep.isSameAsPrevious == False:
      bigText = "RESET"
    else:
      bigText = "CONTINUE"  # Extending a non-divergent path
      self.__currentStep = firstNewIndex # Pick up where we left off

    # Add step to queue
    self._presteps.append(SolutionStep(bigText=bigText, game=self.targetGame))
    self._currentStage = "PRE"
  def __init_poststeps(self):
    bigText = "DONE✅" if self.movesFinishGame else "COLOR?"
    self._poststeps.append(SolutionStep(bigText=bigText, game=self.targetGame))

  def start(self):
    if not self._steps:
      print("No steps to display.")
      return

    running = True
    self.displayCurrent()

    # Main loop
    while running and self._hasNext():

      while True:
        k = readkey() if USE_READCHAR else input()

        if k == 'q' or k == 'Q':
          running = False
        elif k == 'h':
          self.displayHelp()
        elif k == 'n' or k == 'f' or k == ' ' or k == '':
          self.next(wholeStep=(k == 'n'))
        elif USE_READCHAR and (k == key.DOWN or k == key.RIGHT or k == key.ENTER):
          self.next()
        elif k == 'p' or k == 'b':
          self.previous()
        elif USE_READCHAR and (k == key.UP or k == key.LEFT):
          self.previous()
        elif k == 'E':
          self.end()
        elif k == 'r':
          BigSolutionDisplay.__updateScreenWidth()
          self.displayCurrent()
        elif k == 'R':
          self.restart()
        elif k == 'l':
          self.toggleBlindMode()
          self.displayCurrent()
        elif k == 'g' or k.startswith('g'):
          self._acceptGotoCommand(k)
        elif k == 'm':
          self.printValidMoves()
        elif k == 'd':
          self.detailInformation = not self.detailInformation
          if not self.detailInformation:
            self.debugInformation = False
          self.displayCurrent()
          if self.detailInformation:
            self._launchDeadEndComputationBackground()
        elif k == 'D':
          self.debugInformation = not self.debugInformation
          if self.debugInformation:
            self.detailInformation = True
          self.displayCurrent()
          if self.debugInformation:
            self._launchDeadEndComputationBackground(verbose=True)
        elif k == '-' or k.startswith('-'):
          action = self.__acceptGameCommand(k)
          if action is not None:
            print(formatVialColor("wn", "Command not fully supported in this context.") + " This command may not work here, even though it works at other prompts.")
            running = False
        elif k == 't':
          self.performTestCommand()
        else:
          self.printCenteredLines([f"Unrecognized key ({k})"])
          continue  # Keep waiting for a valid key

        break  # We handled a keypress, break out to the main loop

      pass

  def displayHelp(self) -> None:
    B = Style.BRIGHT
    D = Style.DIM
    R = Style.RESET_ALL
    N = Style.NORMAL

    forward = f"{B}f{N} {D}or{N} {B + Style.ITALICS}space{R} {D}or{N} {B}⏎{N}/{B}→{N}/{B}↓{N}"
    backward = f"{B}b{N} {D}or{N} {B}p{N} {D}or{N} {B}←{N}/{B}↑{N}"
    quit = f"{B}q{N} {D}or{N} {B}Q{N}"

    print("Big Solution Display Controls:\n" +
         f"   {quit}                  quit{D}; leave the Big Solution display mode{N}\n" +
         f"   {B}h{N}                       help{D}; reprint this screen{N}\n" +
         f"   {B}n{N}                       forward{D}, to the next step{N}\n" +
         f"   {forward          }     forward\n" +
         f"   {backward   }           backward\n" +
         f"   {B}l{N}                       toggle blind mode{D}; in blind mode, each space must be moved individually{N}\n" +
         f"   {B}r{N}                       refresh display{D}; necessary if the terminal resizes{N}\n" +
         f"   {B}R{N}                       restart solution {D}(to the beginning){N}\n" +
         f"   {B}E{N}                       end solution {D}(to the end){N}\n" +
         f"   {B}m{N}                       moves {D}; print valid moves from the game state{N}\n" +
         f"   {B}d{N}                       details {D}; reveals in-depth game stats{N}\n" +
         f"   {B}D{N}                       debug {D}; shows programmer level status updates{N}\n" +
         f"   {B}t{N}                       Test {D}; does whatever the programmer wants{N}\n" +
         f"   {B}-{N + Style.ITALICS}CMD{R}                    enter game command\n" +
         f"     {B}-help{N}                 print game command help\n")
  def __acceptGameCommand(self, command: str=""):
    curGame = self._getCurStep().game
    if not curGame:
      print(f"{Style.BRIGHT}Game CMD Unavailable{Style.NORMAL} - No game host object")
      return None

    if len(command) <= 1:  # Accept a command received previously, otherwise, receive the rest of the command
      command = "-" + input(Style.BRIGHT + "Game CMD:" + Style.NORMAL + " -")

    if not command or command == "-":
      print("No command received.")
      return None

    return curGame._handleSpecialOption(command)

  def _acceptGotoCommand(self, command: str="") -> None:
    maxIdx = len(self._steps) - 1
    if maxIdx <= 0:
      print(formatVialColor("wn", "Goto unavailable.") + " There are no steps to select from.")
      return

    if len(command) <= 1:  # Accept a command received previously, otherwise, receive the rest of the command
      command = "g" + input(Style.BRIGHT + "Goto step #" + Style.NORMAL)

    if not command or len(command) <= 1:
      print("No step received.")
      return

    stepNum = int(command[1:]) # Assumes a valid integer
    stepIdx = len(self._steps) + stepNum if stepNum < 0 else stepNum - 1
    if stepIdx < 0 or stepIdx > maxIdx:
      print(formatVialColor("er", "Invalid input.") + f" Must enter a number between 1 and {len(self._steps)}. Negative values represent moves from the end of the solution.")
      return

    self._currentStage = "GAME"
    self.__currentStep = stepIdx
    self._currentSpacesMoved = 0
    self.displayCurrent()

  def displayCurrent(self) -> None:
    lines: list[str] = []
    introLines: list[str] = []
    exitLines: list[str] = []

    SIDE_PADDING = " " * 5

    ### INTRO LINES ###

    introLines.append("")
    introLines.append("Level: " + self.rootGame.level)
    if self._earliestSafeStep:
      introLines.append(f"Safe step: {self._earliestSafeStep.game.getDepth()}")
    if self.rootGame.drainMode:
      introLines.append("[Drain Mode]")
    if self.rootGame.blindMode:
      introLines.append("[Blind Mode]")
    if self.rootGame.hadMysterySpaces:
      introLines.append("[Mystery Mode]")
    if self.detailInformation:
      introLines.append("{Details}")
    if self.debugInformation:
      introLines.append("{Debug}")

    ### MAIN CONTENT ###

    lines.append("")
    lines.append("")

    curStep, steps = self._getQueue()
    step = steps[curStep]

    if self._currentStage == "PRE":
      stageLines, color = self._preparePreLines(step)
    elif self._currentStage == "GAME":
      stageLines, color = self._prepareGameLines(step)
      introLines.extend(self._extendIntroLinesGame(step))
    elif self._currentStage == "POST":
      stageLines, color = self._preparePostLines(step)
    else:
      raise "Unknown current stage: " + self._currentStage

    lines.extend(stageLines)
    if not color: color = "bl"

    lines.append("")
    lines.append("")

    ### EXIT LINES ###

    if self._hasNext():
      exitLines.append(Style.DIM + chr(1) + "Press Space to advance. Press 'h' for help. Press 'q' to quit.")
    exitLines.append("")

    ### Print ###

    maxWidth = max(map(len, introLines))
    introLines = [chr(3) + line.ljust(maxWidth) + SIDE_PADDING for line in introLines]

    self.printCenteredLines(lines, linePrefix=formatVialColor(color), linePostfix=Style.RESET_ALL, fullScreenBufferLines=3, introLines=introLines, exitLines=exitLines)
    print("")
  def _preparePreLines(self, step: SolutionStep):
    lines = []
    lines.extend(self._prepareBigCharLines(step.bigText))
    return (lines, None)
  def _prepareGameLines(self, step: SolutionStep):
    lines = []

    # Step counter
    lines.append(Style.BRIGHT + chr(1) + f"Step {self.__currentStep + 1} of {len(self._steps)}:")

    # Additional info
    addlInfo = []
    addlInfo.append(COLOR_NAMES[step.colorMoved])
    addlInfo.append(f'{step.numMoved} space{"" if step.numMoved == 1 else "s"}')
    addlInfo.append(BigSolutionDisplay._getMoveDescriptor(step))
    if step.isSameAsPrevious != None:
      addlInfo.append("Repeated path" if step.isSameAsPrevious else "New path")
    lines.append(" | ".join(addlInfo))

    # Description
    sentences = [
      BigSolutionDisplay._getMoveDescription(step),
      BigSolutionDisplay._getDeadEndSummary(step),
    ]
    sentences = [Style.ITALICS + chr(1) + s for s in sentences if s]
    if sentences:
      lines.append("")
      lines.extend(sentences)

    # Main event
    start, end = step.move
    symbols = f"{start + 1}→{end + 1}"
    lines.extend(self._prepareBigCharLines(symbols))

    # Space dots
    if self._usePerSpaceDots():
      if step.numMoved > 1:
        curMoved = self._currentSpacesMoved if self._currentSpacesMoved else 1
        lines.extend(self._prepareBigDotLines(BigShades.Fill * curMoved + BigShades.Medium * (step.numMoved - curMoved)))
      else:
        lines.extend(self._prepareBigDotLines(None))

    return (lines, step.colorMoved)
  def _preparePostLines(self, step: SolutionStep):
    return self._preparePreLines(step)
  def _extendIntroLinesGame(self, step: SolutionStep) -> list[str]:
    newIntroLines = []

    deadEndsResults = step.deadEndsSearch or self._maxDeadEnds
    if deadEndsResults and deadEndsResults.searchDataAvailable:
      newIntroLines.append("")

      if not self.detailInformation:
        maxDisplay = self.__simpleDeadEndsMax
        deadEndsTxt = f"{maxDisplay}+" if deadEndsResults.numDeadEnds > maxDisplay else deadEndsResults.numDeadEnds
        newIntroLines.append(f"Dead ends: {deadEndsTxt}")
      else:
        if not step.deadEndsSearch:
          detailsDict = {
            "Max dead ends": deadEndsResults.numDeadEnds,
            "Computed step": deadEndsResults.game.getDepth(),
          }
        else:
          prevStep = self._getCurStep(offset=-1)
          prevDeadEnds = None
          if prevStep.deadEndsSearch and prevStep.deadEndsSearch.searchDataAvailable:
            prevDeadEnds = prevStep.deadEndsSearch.numDeadEnds

          deltaEnds = "--"
          if prevDeadEnds is not None:
            deltaEnds = deadEndsResults.numDeadEnds - prevDeadEnds
            if deltaEnds > 0:
              # Negative case already appears properly
              # Zero case should not have a sign
              deltaEnds = "+" + str(deltaEnds)

          detailsDict = {
            "Dead ends": deadEndsResults.numDeadEnds,
            "Delta": deltaEnds,
            "Solutions": deadEndsResults.numEventualSolutions,
            "Search (s)": deadEndsResults.searchSeconds,
            "Iterations": deadEndsResults.searchIterations,
          }

        labelLen = max(map(len, detailsDict.keys())) + 1 # Add one for the colon
        valueLen = max(map(len, map(str, detailsDict.values())))
        for label, value in detailsDict.items():
          newIntroLines.append((label + ":").ljust(labelLen) + " " + str(value).rjust(valueLen))


    return newIntroLines

  @staticmethod
  def _getMoveDescriptor(step: SolutionStep) -> str:
    if step.isComplete:
      return "Complete"
    elif step.vacatedVial:
      return "Vacate"
    elif step.startedVial:
      return "Occupy"
    else:
      return "Move"

  @staticmethod
  def _getMoveDescription(step: SolutionStep) -> str:
    start, end = step.move
    if step.isComplete:
      return f"Complete vial {end+1}"
    elif step.vacatedVial:
      return f"Vacate vial {start+1}"
    elif step.startedVial:
      return f"Occupy vial {end+1}"
    else:
      return ""

  @staticmethod
  def _getDeadEndSummary(step: SolutionStep) -> str:
    r = step.deadEndsSearch
    if not r or not r.searchDataAvailable:
      return ""
    elif not r.hasDeadEnds:
      return "No dead ends - all clear"
    else:
      return ""



  def _prepareBigCharLines(self, symbols: str) -> None:
    bigChars = BigChar.FromSymbols(symbols)
    return ["", *BigChar.FormatSingleLine(*bigChars, spacing=4), ""]

  def _prepareBigDotLines(self, dots: str) -> None:
    if not dots: return [""] * 4 # The dots use four lines of space
    bigChars = BigShades.FromShading(dots)
    return ["", *BigShades.FormatSingleLine(*bigChars, spacing=3), ""]

  def printCenteredLines(self, lines: list[str], linePrefix = "", linePostfix = "", fullScreenBufferLines: int = None, introLines: list[str] = [], exitLines: list[str] = []) -> None:
    """
    Takes an array of lines, centers them, and prints them to the screen.

    :param lines: A list of strings to print. Can contain formatting characters separated from the text by Chr(1).
    :type lines: list[str]
    :param linePrefix: Inserted before every line after centering. Used to control style of all lines.
    :param linePostfix: Appended to each line after centering. Used to reset styles to prevent bleeding of the edge of the space.
    :param fullScreenBufferLines: When specified, full screen mode will be enabled and this number of lines will be withheld.
    :type fullScreenBufferLines: int
    """
    contentHeight = len(lines) + len(introLines) + len(exitLines)
    if fullScreenBufferLines is not None and contentHeight + fullScreenBufferLines < BigSolutionDisplay.SCREEN_HEIGHT:
      extraLines = BigSolutionDisplay.SCREEN_HEIGHT - fullScreenBufferLines - len(lines)

      # Adjust intro lines
      extraLinesPre = extraLines // 2
      if extraLinesPre > len(introLines):
        introLines += [""] * (extraLinesPre - len(introLines))
      else:
        extraLinesPre = len(introLines)

      # Adjust exit lines
      extraLinesPost = extraLines - extraLinesPre
      if extraLinesPost > len(exitLines):
        exitLines = [""] * (extraLinesPost - len(exitLines)) + exitLines

    lines = introLines + lines + exitLines
    lines = [self.__alignContent(line) for line in lines]
    print(linePrefix + (linePostfix + "\n"+linePrefix).join(lines) + linePostfix, flush=True)
  def __alignContent(self, line: str) -> str:
    """
    Takes in a specially formatted line and formats it for printing.

    :param line: The line of data to print. Format "[Style<C1>][Left Aligned<C2>]Middle Aligned (default)[<C3>Right Aligned"]
    :type line: str
    :return: The aligned string ready to print as a single line
    :rtype: str
    """
    # Separate styles from content
    style = ""
    content = line
    if chr(1) in content:
      style, content = content.split(chr(1), maxsplit=1)

    # Split content by alignment
    leftContent = ""
    middleContent = content
    rightContent = ""
    if chr(2) in middleContent:
      leftContent, middleContent = middleContent.split(chr(2), maxsplit=1)
    if chr(3) in middleContent:
      middleContent, rightContent = middleContent.split(chr(3), maxsplit=1)

    # Align content properly
    content = middleContent.center(BigSolutionDisplay.SCREEN_WIDTH)
    if leftContent: content = leftContent + content[len(leftContent):]
    if rightContent: content = content[:-len(rightContent)] + rightContent

    # Recombine and return
    return style + content


  def _launchDeadEndComputationBackground(self, verbose=False) -> None:
    """Safely launches at most one background thread to perform dead end searching."""
    if not self.__needsComputeDeadEndResults():
      if verbose: print("Skipping thread launch because no work necessary")
      return

    with self.__spawnThreadLock:
      if self.__hasSpawnedThread:
        if verbose or self.debugInformation:
          print(formatVialColor("er", "Thread already running.") + " Not creating an extra thread.")
        return

      if not self.__needsComputeDeadEndResults():
        print(formatVialColor("wn", "Unexpected discovery of no work needed.") + "After an initial verification, we acquired a lock and then found no remaining work to do.")
        return

      if verbose or self.debugInformation:
        print("Starting dead processing in a background thread")
      t = threading.Thread(target=self.__computeDeadEndResults)
      t.daemon = True
      t.start()

      self.__hasSpawnedThread = True
  def __needsComputeDeadEndResults(self) -> bool:
    if not self.movesFinishGame or self.__finishedDeadEndsSearch:
      return False
    if self.__hasAdvancedBeyondStep(self.__lastComputedDeadEndStepDepth):
      return False
    return True
  def __hasAdvancedBeyondStep(self, referenceStepDepth: int|None):
    if self._currentStage == "POST":
      return True
    if referenceStepDepth is None:
      return False
    if self._currentStage == "GAME" and self._getCurStep().game.getDepth() >= referenceStepDepth:
      return True
    return False
  def __computeDeadEndResults(self):
    if self.debugInformation:
      print("Computing dead end results for final game states")

    for step in reversed(self._steps):
      if step.deadEndsSearch is not None:
        continue # Avoid duplicative work
      if step.game.getDepth() <= 2:
        self.__finishedDeadEndsSearch = True
        break # We made it all the way to the beginning

      stepDepth = step.game.getDepth()
      results = SafeGameSolver(step.game).analyzeDeadEndStates()
      self.__updateDeadEndResults(step, results)
      self.__lastComputedDeadEndStepDepth = stepDepth
      if self.debugInformation:
        BigSolutionDisplay.PrintDeadEndSearchResults(results)

      if results.numDeadEnds > 9999 or results.searchSeconds > 30:
        self.__finishedDeadEndsSearch = True
        if self.debugInformation:
          print(formatVialColor("wn", "Stopping dead end search.") + " Results are taking too long.")
        break

      if self.__hasAdvancedBeyondStep(stepDepth):
        if self.debugInformation:
          print(formatVialColor("wn", "Stopping dead end search.") + " User has already passed this step.")
        break

      if not self.detailInformation and results.numDeadEnds > self.__simpleDeadEndsMax:
        if self.debugInformation:
          print(formatVialColor("wn", "Stopping dead end search.") + " We've gathered enough information for the simple view.")
        break

    if self.debugInformation:
      print("Computation thread exiting")
    self.__hasSpawnedThread = False
  def __updateDeadEndResults(self, step: SolutionStep, results: DeadEndSearchResults) -> None:
    step.deadEndsSearch = results
    if not self._maxDeadEnds or results.numDeadEnds > self._maxDeadEnds.numDeadEnds:
      self._maxDeadEnds = results
    if not results.hasDeadEnds and (not self._earliestSafeStep or results.game.getDepth() < self._earliestSafeStep.game.getDepth()):
      self._earliestSafeStep = results


  def restart(self) -> None:
    BigSolutionDisplay.__updateScreenWidth()
    if not self._hasPrev():
      print("Already at the first step.")
      return

    self.__currentStep = 0
    self.__currentPoststep = 0
    self._currentSpacesMoved = 0
    self._currentStage = "GAME"
    self.displayCurrent()
  def end(self) -> None:
    self.__currentPoststep = 0
    self._currentStage = "POST"
    self.displayCurrent()
  def next(self, wholeStep=False) -> None:
    if not self._hasNext():
      print("Already at the last step.")
      return

    curStep, steps = self._getQueue()
    numToMove = steps[curStep].numMoved

    partialStepsEnabled = not wholeStep and self._usePerSpaceDots() and numToMove > 1
    if partialStepsEnabled and self._currentSpacesMoved < numToMove:
      self._currentSpacesMoved += 1 if self._currentSpacesMoved else 2 # If set to zero, it was treated as 1 anyways
    else:
      self._currentSpacesMoved = 1
      if curStep < len(steps) - 1:
        self._setStep(curStep+1)
      elif self._currentStage == "PRE":
        self._currentStage = "GAME"
      elif self._currentStage == "GAME":
        self._currentStage = "POST"

    self.displayCurrent()
  def previous(self) -> None:
    if not self._hasPrev():
      print("Already at the first step.")
      return

    curStep, _steps = self._getQueue()
    # Don't walk backward through individual spaces
    if curStep > 0:
      self._setStep(curStep-1)
    elif self._currentStage == "POST":
      self._currentStage = "GAME"
    elif self._currentStage == "GAME":
      self._currentStage == "PRE"

    # Always set the spaces to "all moved"
    numToMove = self._getCurStep().numMoved
    self._currentSpacesMoved = numToMove if numToMove else 0

    self.displayCurrent()

  def _hasNext(self) -> bool:
    if self._currentStage == "PRE":
      return True # Always have a GAME stage

    curStep, steps = self._getQueue()
    if curStep < len(steps) -1:
      return True # There are remaining steps in this stage

    if self._currentStage == "POST":
      return False # Post is the last stage

    return len(self._poststeps) > 0 # The POST stage is available
  def _hasPrev(self) -> None:
    if self._currentStage == "POST":
      return True # Always have a GAME stage

    curStep, _steps = self._getQueue()
    if curStep > 0:
      return True # There are previous steps in this stage

    return False # Cannot return from GAME nor PRE stages
  def _getQueue(self) -> tuple[int, deque["SolutionStep"]]:
    if self._currentStage == "PRE":
      return (self.__currentPrestep, self._presteps)
    elif self._currentStage == "GAME":
      return (self.__currentStep, self._steps)
    elif self._currentStage == "POST":
      return (self.__currentPoststep, self._poststeps)
    else:
      raise "Unknown current stage: " + self._currentStage
  def _getCurStep(self, offset: int = 0) -> SolutionStep:
    curStep, steps = self._getQueue()
    return steps[curStep + offset]
  def _setStep(self, newStep) -> None:
    if self._currentStage == "PRE":
      self.__currentPrestep = newStep
    elif self._currentStage == "GAME":
      self.__currentStep = newStep
    elif self._currentStage == "POST":
      self.__currentPoststep = newStep
    else:
      raise "Unknown current stage: " + self._currentStage

  def _usePerSpaceDots(self) -> bool:
    return self.rootGame.blindMode
  def toggleBlindMode(self) -> None:
    self.rootGame.blindMode = not self.rootGame.blindMode
    self.rootGame.modified = True
    saveGame(self.rootGame)

  def performTestCommand(self) -> None:
    print("Executing test command")

    curStep = self._getCurStep()
    print(f"Searching for dead ends from current point")

    safeSolver = SafeGameSolver(curStep.game)
    r = safeSolver.analyzeDeadEndStates()
    self.__updateDeadEndResults(curStep, r)
    if r.searchDataAvailable:
      BigSolutionDisplay.PrintDeadEndSearchResults(r)

    if safeSolver.deadEndsLocated:
      displayIndex = 0
      printInformation = True
      while displayIndex < len(safeSolver.deadEndsLocated) and displayIndex >= 0:
        if printInformation:
          print(f"\nDisplaying dead end {displayIndex+1} of {len(safeSolver.deadEndsLocated)}: {Style.DIM}(Next, Prev. 'Enter' exits){Style.NORMAL}")
          deadEnd = safeSolver.deadEndsLocated[displayIndex]
          deadEnd.printVials()
          deadEnd.printMoves(curStep.game)
        printInformation=True

        print("% ", end="", flush=True)
        k = readkey() if USE_READCHAR else input().strip()
        if k == '' or k == 'q' or k == 'Q' or (USE_READCHAR and k == key.ENTER):
          break
        elif k == 'n' or k == 'f':
          if displayIndex>=len(safeSolver.deadEndsLocated)-1:
            print("No next dead ends to explore.")
            printInformation=False
            continue
          displayIndex += 1
        elif k == 'p' or k == 'b':
          if displayIndex<=0:
            print("No previous dead ends to explore.")
            printInformation=False
            continue
          displayIndex -= 1
        else:
          print(f"Unrecognized key ({k})")
          printInformation=False

    print("☠️ Dead ends ahead" if r.hasDeadEnds else "🟢 All clear")
  def _reportDeadEnd(self, seed: "Game", deadEnd: "Game") -> None:
    deadEnd.printMoves()

  def printValidMoves(self) -> None:
    lines = []
    curGame = self._getCurStep().game.prev
    nextGames = curGame.generateNextGames()

    lines.append(f"All valid moves ({len(nextGames)}):")
    lines.extend(["  " + game.getMoveString(SolutionStep(game)) for game in nextGames])

    curGame.printVials()
    print("\n".join(lines))

  @staticmethod
  def PrintDeadEndSearchResults(r: DeadEndSearchResults) -> None:
    if not r.searchDataAvailable:
      print(f"Did not search. Has dead ends={r.hasDeadEnds} (step {r.game.getDepth()})")
      return

    iterations = formatVialColor("bold", f"{r.searchIterations} iterations")
    deadEnds = formatVialColor("er" if r.hasDeadEnds else "wn", f"{r.numDeadEnds} dead ends")
    solutions = formatVialColor("bold", f"{r.numEventualSolutions} solutions")
    searchTime = formatVialColor("bold", f"{r.searchSeconds} seconds")

    print(f"Searched {iterations} and found {deadEnds} and {solutions} in {searchTime} (step {r.game.getDepth()})")

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

class BaseSolver:
  SOLVE_METHODS = Literal["MIX","BFS","DFS","DFR"]

  # Inputs/parameters
  seedGame: Game
  # solveMethod: "SOLVE_METHODS"
  findSolutionCount = 1

  # Solution Set stats
  solutionSetStart: float
  solutionSetEnd: float
  solutionStart: float
  solutionEnd: float

  minSolution: Game = None
  solutionsAttempted: int = 0
  minSolutionUpdates: int
  numSolutionsAbandoned: int

  # Solution Solution status
  numIterations: int
  numDeadEnds: int
  numPartialSolutionsGenerated: int
  numSwallowedGamesFound: int
  numUniqueStatesComputed: int
  numDuplicateGames: int
  maxQueueLength: int

  # Analysis summary data structures
  partialDepth = defaultdict(int)
  dupGameDepth = defaultdict(int)
  swallowedDepth = defaultdict(int)
  deadEndDepth = defaultdict(int)
  solutionDepth = defaultdict(int)
  uniqueSolsDepth = defaultdict(int)
  solFindSeconds = defaultdict(int)
  uniqueSolutions: defaultdict[int, list["Game"]] = defaultdict(list)
  isUniqueList: list[bool] = list()

  # Solving data
  _searchBFS: bool
  _q: deque["Game"]
  _findSolutionsRemaining: int
  REPORT_ITERATION_FREQ: int
  QUEUE_CHECK_FREQ: int
  REPORT_SEC_FREQ: int

  def __init__(self, game: "Game"):
    self.seedGame = game

  def setSolveMethod(self, newSolveMethod: SOLVE_METHODS) -> None:
    raise "Method not yet implemented"

  def solveGame(self, solveMethod: SOLVE_METHODS = "MIX", numSolutions: int = 1) -> None:
    if numSolutions < 1: numSolutions = 1
    self.findSolutionCount = numSolutions
    self._findSolutions(solveMethod)
    self._onAfterFindSolutions()
    saveGame(self.seedGame)

  def _findSolutions(self, solveMethod: SOLVE_METHODS, suppressSolveMethodNotification=False):
    """
    Intelligent search through all the possible game states until we find a solution.
    The game already handles asking for more information as required.
    """
    setSolveMethod(solveMethod, suppressNotification=suppressSolveMethodNotification)
    # self.solveMethod = solveMethod

    self.solutionSetStart = None
    self.solutionSetEnd = None
    self.solutionStart = None
    self.solutionEnd = None

    self.minSolutionUpdates = 0
    self.numSolutionsAbandoned = 0

    self._findSolutionsRemaining = self.findSolutionCount

    # Analyzing variables
    self.solutionSetStart = time()
    self.deadEndDepth[1]

    self.REPORT_ITERATION_FREQ = 10000 if SOLVE_METHOD == "BFS" else 1000
    self.QUEUE_CHECK_FREQ = self.REPORT_ITERATION_FREQ * 10
    self.REPORT_SEC_FREQ = 15

    # Time check setup
    timeCheck: float
    computed: set["Game"]|None = None


    while Game.reset or not self.minSolution or self._findSolutionsRemaining > 0:
      Game.reset = False
      if not self._onInitSolutionAttempt():
        break

      self.solutionsAttempted += 1
      self._findSolutionsRemaining -= 1

      self.solutionStart = time()
      expectSolution = True

      # Setup our search
      solution: Game | None = None
      self._q = deque()
      computed = set()
      self._searchBFS = False
      if Game.latest:
        self._q.append(Game.latest)
        Game.latest = None
        self._searchBFS = True
        expectSolution = False
      else:
        self._q.append(self.seedGame)
        self._searchBFS = self._shouldSearchBFS()

      self.numIterations = 0
      self.numDeadEnds = 0
      self.numPartialSolutionsGenerated = 0
      self.numSwallowedGamesFound = 0
      self.numDuplicateGames = 0
      self.maxQueueLength = 1

      # CONSIDER: Switching our approach based on the state of the game
      # When we still have unknowns, we should find the shortest path to find an unknown,
      # and continue in that same path until we reach a dead end.
      # This makes it easier for a human to follow along in the game

      # Perform the search
      while self._q and not solution:
        # Break out
        if Game.reset or Game.quit:
          expectSolution = False
          break

        # Taking from the front or the back makes all the difference between BFS and DFS
        current = self._q.popleft() if self._searchBFS else self._q.pop()

        # Perform some work at some checkpoints
        self.numIterations += 1
        if self.numIterations % self.REPORT_ITERATION_FREQ == 0:
          continueSearching = self._onIterationReport(current)
          if not continueSearching:
            expectSolution = False
            self._findSolutionsRemaining = 0

        # Prune if we've found a cheaper solution
        if not self._searchBFS and self.minSolution and self.minSolution._numMoves <= current._numMoves:
          self.numSolutionsAbandoned += 1
          break # Quit this attempt, and try a different one

        # Check all next moves
        hasNetNewNextGame = False
        nextGames = current.generateNextGames()
        if Game.reset or Game.quit:
          # Break out after user input
          expectSolution = False
          break

        if SHUFFLE_NEXT_MOVES: random.shuffle(nextGames)
        for nextGame in nextGames:
          self.numPartialSolutionsGenerated += 1
          self.partialDepth[nextGame._numMoves] += 1

          if nextGame in computed:
            self.numDuplicateGames += 1
            self.dupGameDepth[nextGame._numMoves] += 1
            continue
          computed.add(nextGame)

          hasNetNewNextGame = True
          if nextGame.isFinished():
            timeCheck = time()
            self.solutionEnd = timeCheck
            if self._onSolutionFound(nextGame):
              break # Finish searching
          else:
            self._q.append(nextGame)

        # Maintain stats
        self.maxQueueLength = max(self.maxQueueLength, len(self._q))
        if len(nextGames) == 0:
          self.numDeadEnds += 1
          self.deadEndDepth[current._numMoves] += 1
          self._onDeadEndFound(current)
        elif not hasNetNewNextGame:
          self.numSwallowedGamesFound += 1
          self.swallowedDepth[current._numMoves] += 1

      self.solutionEnd = time()
      if expectSolution and not self.minSolution:
        tryAgain = self._onImpossibleGame()
        if not tryAgain:
          break # There are no solutions

      pass

    self.solutionSetEnd = time()
    self.numUniqueStatesComputed = len(computed) if computed else 0

  def _shouldSearchBFS(self) -> bool:
    if SOLVE_METHOD == "BFS" or SOLVE_METHOD == "MIX":
      return True
    elif SOLVE_METHOD == "DFS" or SOLVE_METHOD == "DFR":
      return False
    else:
      raise Exception("Unrecognized solve method: " + SOLVE_METHOD)

  def _onInitSolutionAttempt(self, bypassErrorCorrection = False) -> bool:
    """Called before attempting a new solution. Return True to proceed with the solution."""
    # First correct any errors in the game
    if not bypassErrorCorrection and self.seedGame.attemptCorrectErrors():
      return False
    return True

  def _onIterationReport(self, current: Game) -> bool:
    """Called when the iteration search count exceeds REPORT_ITERATION_FREQ. Return True to continue searching."""
    if not self._searchBFS:
      print(f"Checked {self.numIterations} iterations.")
    return True

  def _onSolutionFound(self, solution: Game) -> bool:
    """Called when a new solution is found. Return True to stop this attempt with the discovered solution"""
    if not self.minSolution or solution._numMoves < self.minSolution._numMoves:
      self.minSolution = solution
      self.minSolutionUpdates += 1
    self.solutionDepth[solution._numMoves] += 1
    self.solFindSeconds[int((self.solutionEnd - self.solutionStart + 0.9) // 1)] += 1

    solutionHash = solution._completion_hash()
    hashingList = self.uniqueSolutions[solutionHash]
    if not len(hashingList):
      self.uniqueSolsDepth[solution._numMoves] += 1
      self.isUniqueList.append(True)
    else:
      self.isUniqueList.append(False)
    hashingList.append(solution)

    return True

  def _onDeadEndFound(self, deadEnd: Game) -> None:
    pass

  def _printQueueCheck(self, current: Game) -> None:
    stats = {
      "resets": self.solutionsAttempted,
      "itrs": self.numIterations,
      "mvs": current._numMoves,
      "q len": len(self._q),
      "ends": self.numDeadEnds,
      "dup games": self.numDuplicateGames,
      "mins": round((time() - self.solutionStart) / 60, 1)
    }
    stats_str = "\t".join(f"{stat}: {value}" for stat, value in stats.items())
    print(f"QUEUE CHECK: \t{stats_str}")

  def _onImpossibleGame(self) -> bool:
    """Called when the it is detected that no solutions exist. Return true to reset and try again."""
    message = formatVialColor("er", "This game has no solution.")
    message += " Type YES if you have corrected the game state and want to try searching again."
    retryRsp = self.seedGame.requestVal(message, printOptions=True, printState=False)
    return retryRsp == "YES"

  def _onAfterFindSolutions(self) -> None:
    """Called after _findSolutions() completes. Use this to report on the discovered solution."""

    # Override me.
    self._printQueueCheck()
    print(f"Found solution requiring {self.minSolution.getDepth()} moves.")

  @staticmethod
  def _getTimeRunning(startTime: float, endTime: float) -> tuple[float, float]: # (seconds, minutes)
    seconds = round(endTime - startTime, 1)
    minutes = round((endTime - startTime) / 60, 1)
    return (seconds, minutes)

class AnalysisSolver(BaseSolver):
  lastReportTime = 0

  def _onInitSolutionAttempt(self):
    if not super()._onInitSolutionAttempt(bypassErrorCorrection=True):
      return False

    timeCheck = time()
    if self._findSolutionsRemaining % 1000 == 0 or timeCheck - self.lastReportTime > self.REPORT_SEC_FREQ:
      print(f"Searching for {self._findSolutionsRemaining} more solutions. Running for {round(timeCheck - self.solutionSetStart, 1)} seconds. ")
      self.lastReportTime = timeCheck
    return True

  def _onIterationReport(self, current):
    # Suppress the default status check behavior
    # super()._onIterationReport(current)
    return True


  def _onAfterFindSolutions(self):
    secsAnalyzing, minsAnalyzing = BaseSolver._getTimeRunning(self.solutionSetStart, self.solutionSetEnd)

    # Print out interesting information to the console only
    print("")
    minSolutionMoves, maxSolutionMoves, modeSolutionMoves, countUniqueSols = analyzeCounterDictionary(self.uniqueSolsDepth)
    minDeadEnd, lastDeadEnd, modeDeadEnds, _ = analyzeCounterDictionary(self.deadEndDepth)
    nDupSols = self.findSolutionCount - countUniqueSols
    minFindTime, maxFindTime, modeFindTime, _ = analyzeCounterDictionary(self.solFindSeconds)

    # printUniqueSolutions(uniqueSolutions)

    printCounterDict(self.solFindSeconds, title="Time to find Solutions:")

    print(f"""
        Finished analyzing solution space:
          * Note: These values are counted as independent occurrences. It's possible that
            the same states from multiple distinct samples found the same sets of game states.

          Report:
          {self.findSolutionCount       }\t   Analysis samples
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
          {fPercent(nDupSols, self.findSolutionCount)}\t   Percent duplicated solutions
          """)

    # Identify and prepare some extra data
    extraDataLen = identifyExtraDataLength(self.partialDepth)
    longestSolvesDict = prepareLongestSolves(extraDataLen, self.solFindSeconds)
    uniqueDistributionDict = prepareUniqueDistribution(extraDataLen, self.isUniqueList)
    completionData = prepareCompletionOrderData(self.seedGame, self.uniqueSolutions)

    saveAnalysisResults(\
      self.seedGame, self.solutionSetEnd - self.solutionSetStart, self.findSolutionCount, \
      self.partialDepth, self.dupGameDepth, self.deadEndDepth, self.solutionDepth, self.uniqueSolsDepth, self.swallowedDepth, \
      longestSolvesDict, uniqueDistributionDict, completionData, \
      self.solFindSeconds)

class SolutionSolver(BaseSolver):
  # Static
  MysteryContinuation = False

  def _onInitSolutionAttempt(self):
    if not super()._onInitSolutionAttempt(bypassErrorCorrection=True):
      return False

    if self.minSolution and SolutionSolver.MysteryContinuation:
      # NOTE: If self._searchBFS has already been turned off, we ended up in DFR mode.
      # Consider allowing the additional search attempts to proceed in this case.
      return False
    return True
  def _onIterationReport(self, current):
    if not super()._onIterationReport(current):
      return False

    if SOLVE_METHOD == "MIX" and self._searchBFS and current._numMoves >= MIX_SWITCH_THRESHOLD_MOVES:
      self._searchBFS = False
      print("Switching to DFS search for MIX solve method")
    elif self.numIterations % self.QUEUE_CHECK_FREQ == 0:
      if ENABLE_QUEUE_CHECKS and not self._searchBFS:
        return current.confirmPrompt("This is a lot. Would you like to continue searching?")

      self._printQueueCheck(current)
      if SOLVE_METHOD == "MIX":
        switchFaster = current.confirmPrompt("This is a lot. Would you like to switch to a faster approach?", defaultYes=False)
        if switchFaster:
          self._searchBFS = False
          setSolveMethod("DFS")

    return True


  def _onAfterFindSolutions(self):
    secsSearching, minsSearching = BaseSolver._getTimeRunning(self.solutionStart, self.solutionEnd)
    shortestSolutionLen = self.minSolution._numMoves if self.minSolution else "--"

    print(f"""
          Finished search algorithm:

            Overall:
            {SOLVE_METHOD                 }\t   Solving method
            {self.solutionsAttempted      }\t   Num solutions attempted
            {shortestSolutionLen          }\t   Shortest Solution
            {self.minSolutionUpdates      }\t   Min solution updates
            {self.numSolutionsAbandoned   }\t   Num solutions abandoned

            Since last reset:
            {secsSearching                }\t   Seconds searching
            {minsSearching                }\t   Minutes searching
            {self.numIterations           }\t   Num iterations
            {len(self._q)                 }\t   Ending queue length
            {self.maxQueueLength          }\t   Max queue length
            {self.numDeadEnds             }\t   Num dead ends
            {self.numPartialSolutionsGenerated }\t   Partial solutions generated
            {self.numSwallowedGamesFound       }\t   Num swallowed games
            {self.numDuplicateGames            }\t   Num duplicate games
            {self.numUniqueStatesComputed      }\t   Num states computed
          """)

    if self.minSolution:
      BigSolutionDisplay(self.minSolution).start()
      # print(f"Found solution{' to level ' + game.level if game.level else ''}!")
      # self.minSolution.printMoves()
    else:
      print(formatVialColor("er", "Cannot find solution."))

class SafeGameSolver(BaseSolver):
  """Specialized solver equipped to determine if a partially solved game has any remaining dead ends."""
  numSolutionsLocated: int
  deadEndsLocated: list["Game"]

  def __init__(self, game):
    super().__init__(game)

    self.numSolutionsLocated = 0
    self.deadEndsLocated = []

  def _onInitSolutionAttempt(self):
    # Bypass
    if self.seedGame.getDepth() <= 1:
      self.numDeadEnds = 1 # Initialize to avoid errors
      print(formatVialColor("er", "Expected game near completion.") + " This game is unsolved and certainly is not safe.")
      return False
    return True

  def _onSolutionFound(self, solution):
    self.numSolutionsLocated += 1
    return False # Avoid registering this solution, and keep looking for dead-ends

  def _onDeadEndFound(self, deadEnd):
    self.deadEndsLocated.append(deadEnd)

  def _onImpossibleGame(self):
    pass # This solver never saves solutions, and will always report "impossible"

  def solveGame(self, solveMethod = "MIX", numSolutions = 1):
    raise "Method not supported"

  def searchForAnyDeadEnd(self) -> bool:
    """Searches any combination of moves that would result in a dead end. Returns true if any are found."""
    if self.seedGame.isFinished():
      return False
    self.findSolutionCount = 1
    self._findSolutions("BFS", suppressSolveMethodNotification=True)
    return self.numDeadEnds > 0

  def analyzeDeadEndStates(self) -> DeadEndSearchResults:
    """Searches any combination of moves that would result in a dead end. Returns {DeadEndSearchResults} representing the findings."""
    self.searchForAnyDeadEnd()
    return self.exportDeadEndSearchResults()

  def exportDeadEndSearchResults(self) -> DeadEndSearchResults:
    try:
      searchSeconds, _ = SafeGameSolver._getTimeRunning(self.solutionSetStart, self.solutionSetEnd)
      return DeadEndSearchResults(self.seedGame, self.numIterations, searchSeconds, self.numDeadEnds, self.numSolutionsLocated)
    except:
      # Not all of these properties are available when the game is complete
      return DeadEndSearchResults(self.seedGame, 0, 0, 0, 0, searchDataAvailable=False)



def solveGame(game: "Game", solveMethod = "MIX", analyzeSampleCount = 0, probeDFRSamples = 0):
  solver = AnalysisSolver(game) if analyzeSampleCount > 0 else SolutionSolver(game)
  solver.solveGame(solveMethod, numSolutions=analyzeSampleCount or probeDFRSamples)
  pass

def testSolutionPrints(solution: "Game"):
  # Requires that the solution have at least 10 moves to solve
  solution.getNthParent(10).printMoves()
  solution.getNthParent(5).printMoves()
  solution.getNthParent(2).printMoves()
  solution.getNthParent(0).printMoves()

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


def readGameInput(userInteracting: bool, drainMode: bool = None, blindMode: bool = None) -> Game:
  game = _readGame(input, userInteraction=userInteracting, drainMode=drainMode, blindMode=blindMode)
  game.modified = True
  return game
def readGameFile(gameFileName: str, level: str = None, drainMode: bool = None, blindMode: bool = None) -> Game:
  gameRead: Game = None
  try:
    gameFile = open(gameFileName, "r")
    nextLine = lambda: gameFile.readline().strip()

    mode = nextLine()                       # Read mode
    if mode == "i":
      levelLine = nextLine().split()        # Read level name
      level = levelLine[0]
      drainMode = "drain" in levelLine or "pour" in levelLine
      blindMode = "blind" in levelLine
      mysteryMode = "mystery" in levelLine
    gameRead = _readGame(nextLine, drainMode=drainMode, blindMode=blindMode)
    gameRead.level = level
    if mysteryMode: gameRead.hadMysterySpaces = True

    gameFile.close()
  except FileNotFoundError:
    print("Attempted to resume progress, but no file exists for this level.")
    # The file doesn't exist, just ask for it from the user
  else:
    print("Resumed game progress from saved file " + gameFileName)
  finally:
    return gameRead
def _readGame(nextLine: Callable[[], str], userInteraction = False, drainMode: bool = None, blindMode: bool = None) -> Game:
  """
  Reads the game one line at a time by invoking a configurable `nextLine()` method.

  Users are presented with nice prompts asking for each piece of information.
  With users, the number of vials is determined based on when an empty line is parsed.

  When reading from files, the prompts are suppressed and the number of vials is
  explicitly read as the first line of input.
  """
  if drainMode is None:
    drainMode = False
    if userInteraction:
      rsp = input("Level uses drain gameplay? (y/n): ").strip().lower()
      if rsp and rsp[0] == "y":
        drainMode = True
  if drainMode and userInteraction:
    print("Reading a drain-mode game.")

  if blindMode is None:
    blindMode = False
    if userInteraction:
      rsp = input("Level uses blind gameplay? (y/n): ").strip().lower()
      if rsp and rsp[0] == "y":
        blindMode = True
  if blindMode and userInteraction:
    print("Reading a blind-mode game.")

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
  if userInteraction: printVialEntryIntro()

  emptyRest = False
  i = 0
  while i < numVials or numVials == -1:
    i += 1
    if numVials != -1 and (emptyRest or i > numVials - numEmpty):
      vials.append(["-"] * NUM_SPACES_PER_VIAL)
      continue

    if userInteraction: print(f"Vial {i}: ")
    response = nextLine().strip()
    if response == "" or not response:
      emptyRest = True
      i -= 1 # Place an empty value for this row
      if userInteraction:
        numVials = len(vials) + _determineNumEmpty(len(vials))
      continue

    if response == ".":
      vials.append(["?"] * NUM_SPACES_PER_VIAL)
      continue

    spaces = response.split()
    if len(spaces) > NUM_SPACES_PER_VIAL:
      if len(vials) > 0:
        print(formatVialColor("er", "Too many colors.") + f" The game only supports {NUM_SPACES_PER_VIAL} colors per vial.")
        continue

      # Mystery input mode where only the first color of each vial is observable
      for topColor in spaces:
        vials.append([topColor] + ["?"] * (NUM_SPACES_PER_VIAL - 1))
      i = len(vials) # Jump forward for all the vials we created
      numVials = len(vials) + _determineNumEmpty(len(vials))
      emptyRest = True
      continue

    while len(spaces) < NUM_SPACES_PER_VIAL:
      spaces.append("?")
    vials.append(spaces)

  return Game.Create(vials, drainMode=drainMode, blindMode=blindMode)
def printVialEntryIntro() -> None:
  print(Fore.CYAN +
    f"On the next lines, please type {NUM_SPACES_PER_VIAL} words representing the colors in each vial from top to bottom.\n"+
    "  Stopping short of the depth of a vial will fill the remaining spaces with question marks.\n" +
    "  Type a . (period) to insert a whole row of question marks.\n" +
    "  Type a blank line signal that all vials with colors have been represented (all remaining vials are empty).\n" + Fore.RESET)

  COLUMNS = 3
  CODE_WIDTH = 4
  NAME_WIDTH = 20

  availableColorsKeys = sorted([k for k in COLOR_NAMES.keys() if k not in RESERVED_COLORS])
  colorsPerCol = ceil(len(availableColorsKeys) / COLUMNS)
  lines: list[str] = ["  "] * colorsPerCol

  for idx, k in enumerate(availableColorsKeys):
    lines[idx % colorsPerCol] += Style.BRIGHT + formatVialColor(k, k, CODE_WIDTH, foregroundOnly=True) + Style.NORMAL + formatVialColor(k, COLOR_NAMES[k], NAME_WIDTH, foregroundOnly=True)

  lines.insert(0, "Available colors:")
  lines.append("")
  print("\n".join(lines))
def _determineNumEmpty(vialsWithColors: int) -> int:
  return 1 if vialsWithColors < FEW_VIALS_THRESHOLD else 2

def chooseInteraction():
  validModes = set("psqin")
  mode: str = None
  level: str = None
  drainMode: bool = False  # None means ask the user; otherwise, True/False
  blindMode: bool = False  # None means ask the user; otherwise, True/False
  userInteracting = True
  game: Game = None
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
      # Determine special modes
      if "drain" in sys.argv:
        drainMode = True
        sys.argv.remove("drain")
      if "blind" in sys.argv:
        blindMode = True
        sys.argv.remove("blind")

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
          p LEVEL?                  play
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
    elif firstWord == "p":
      mode = "p"
      if len(words) > 1:
        level = words[1]
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
    game = readGameFile(gameFileName, level, drainMode=drainMode, blindMode=blindMode)

  if game and level:
    game.level = level


  # Fallback to reading in manually
  if not game:
    game = readGameInput(userInteracting, drainMode=drainMode, blindMode=blindMode)
    if level != None:
      game.level = level
    saveGame(game)

  # Verify game has no error
  if game.attemptCorrectErrors():
    print("Attempts to resolve the errors did not work. Abandoning program.")
    return

  # Choose mode
  if mode == "p":
    playGame(game)
  elif mode == "i" or mode == "s" or mode == "n":
    solveGame(game, solveMethod=SOLVE_METHOD, probeDFRSamples=dfrSearchAttempts)
    saveGame(game)
  elif mode == "a":
    solveGame(game, solveMethod="DFR", analyzeSampleCount=analyzeSamples)
  else:
    print("Unrecognized mode: " + mode)

  quit(0)
def debugLevel(level,dfrSearchAttempts=DFR_SEARCH_ATTEMPTS):
  print(f"\n\nDEBUGGING LEVEL: {level}\n\n")
  gameFileName = generateFileName(level)
  originalGame = readGameFile(gameFileName, level)
  originalGame.level = level
  solveGame(originalGame, solveMethod=SOLVE_METHOD, probeDFRSamples=dfrSearchAttempts)
  saveGame(originalGame)

def saveGame(game: "Game", forceSave = False) -> None:
  if not game or not game.level or (not forceSave and not game.modified):
    return None # No saving necessary
  fileName = generateFileName(game.level)
  result = generateFileContents(game)
  saveFileContents(fileName, result)
  game.modified = False
  print(f"Saved discovered game state to file: {fileName}")
def getBasePath(absolutePath = WRITE_FILES_TO_ABSOLUTE_PATH) -> str:
  return INSTALLED_BASE_PATH if absolutePath else ""
def annualizeDailyPuzzleFileName(levelNum: str) -> str:
  if levelNum[0:3].lower() in MONTH_ABBRS:
    year = datetime.now().year
    return os.path.join(str(year),levelNum)
  return levelNum
def generateFileName(levelNum: str, absolutePath: bool = None) -> str:
  annualizedName = annualizeDailyPuzzleFileName(levelNum)
  return os.path.join(getBasePath(absolutePath),"wslevels",f"{annualizedName}.txt")
def generateFileContents(game: "Game") -> str:
  lines = list()
  lines.append("i")

  levelLine = str(game.level)
  levelModes = game.specialModes
  if levelModes: levelLine += " " + " ".join(levelModes)

  lines.append(levelLine)
  lines.append(str(len(game.vials)))
  for vial in game.vials:
    lines.append("\t".join(vial))
  # lines.append("")
  return "\n".join(lines)
def saveFileContents(fileName: str, contents: str) -> None:
  # Ensure parent folders exist
  directory_path = os.path.dirname(fileName)
  if not os.path.exists(directory_path):
      os.makedirs(directory_path, exist_ok=True)

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
def setSolveMethod(method: str, suppressNotification=False) -> bool:
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

  if not suppressNotification: print("Set solve method to " + method)
  return True

def generateAnalysisResultsName(level: str, absolutePath: bool = None) -> str:
  annualizedName = annualizeDailyPuzzleFileName(level)
  return os.path.join(getBasePath(absolutePath), "wsanalysis", f"{annualizedName}-{round(time())}.csv")
def saveAnalysisResults(rootGame: Game, seconds: float, samples: int,
                        partialStates, dupStates, deadStates, solStates, uniqueSolStates, swallowedGames,
                        longestSolves, uniqueSolsDistribution, completionData: tuple[defaultdict[int, str], defaultdict[int, str]],
                        solveTimes: defaultdict[int] = None) -> None:
  # Generates a CSV file with data
  # This spreadsheet has been setup to analyze these data exports
  # https://docs.google.com/spreadsheets/d/1HK8ic2QTs1onlG_x7o9s0yXxY1Nl9mFLO9mHtou2RcA/edit#gid=1119310589

  extraDataLength = max(
    max(longestSolves.keys()),
    max(uniqueSolsDistribution.keys()))

  fileName = generateAnalysisResultsName(rootGame.level)
  specialModes = rootGame.specialModes
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
    ("Modes", ";".join(specialModes) if specialModes else "normal"),
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
    ("Swallowed Game States", swallowedGames)
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
def preserveHighestOrderDigits(x: int, digits=5) -> int:
  """
  Given an int with any number of digits (base 10),
  It will return at most the `digits` number of the highest order digits
  """
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

def formatVialColor(color: str, text: str = "", ljust=0, foregroundOnly=False) -> str:
  """Formats a color for printing. If text is provided, it will autoreset the style afterwards as well."""
  out = (COLOR_FOREGROUND if foregroundOnly else COLOR_CODES)[color]
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

# GAMEPLAY_MODE can appear anywhere in the list
# py watersort.py <GAMEPLAY_MODE?> LEVEL <MODE>
# py watersort.py LEVEL <GAMEPLAY_MODE?> <MODE>
# py watersort.py LEVEL <MODE> <GAMEPLAY_MODE?>
# py watersort.py <GAMEPLAY_MODE?> LEVEL dfr SAMPLES?
chooseInteraction()

# debugLevel("dec15", dfrSearchAttempts=1)
