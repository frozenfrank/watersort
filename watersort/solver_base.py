
from collections import deque
from enum import Enum, auto
from random import shuffle
from time import time
from typing import TypedDict
from personal.watersort.game import Game
from personal.watersort.snippet import getTimeRunning

DFR_DEFAULT_SEARCH_ATTEMPTS = 10000
ENABLE_QUEUE_CHECKS = True # Disable only for temporary testing

class SolveMethod(Enum):
  MIX = auto() # BFS first, then DFS after a threshold
  BFS = auto() # Breadth First Search
  DFS = auto() # Depth First Search
  DFR = auto() # Depth First Randomized
  DEFAULT = MIX

  @classmethod
  def Interpret(cls, name: str) -> "SolveMethod":
    name = name.upper()
    # if not cls.hasKey(name):
    #   return None
    return SolveMethod[name]

  @classmethod
  def hasKey(cls, key: str) -> bool:
    # https://stackoverflow.com/a/62065380/2844859
    return key in cls.__members__

  @classmethod
  def getKeys(cls) -> list[str]:
    return list(cls.__members__.keys())

class HasTimerStats(TypedDict):
  startTime: float
  endTime: float
class SolveStats(HasTimerStats): # sv
  root: Game
  numResets: int
  allSolutions: list[Game] # Sometimes empty
  uniqueSolutions: set[Game]

  minSolution: Game
  minSolutionUpdates: int
  numSolutionsAbandoned: int
class SolutionStats(HasTimerStats): # st
  q: deque[Game]
  solution: Game
  computed: set[Game]

  numIterations: int
  numDeadEnds: int
  numDuplicateGames: int
  numPartialSolutionsGenerated: int
  maxQueueLength: int

class Solver:
  # These apply to all instances, but can be overridden on individual instances

  # Solver config
  _solveMethod = SolveMethod.DEFAULT
  shuffleMoves = False
  findSolutionCount = 1
  preserveAllSolutions = False

  MIX_SWITCH_THRESHOLD_MOVES = 10

  # Others
  silentSuccessMessages = False

  # Solving Data (these params may be mutated by subclasses as necessary)
  REPORT_ITERATION_FREQ: int
  QUEUE_CHECK_FREQ: int
  searchBFS: bool
  solveStats: SolveStats
  lastSolutionStats: SolutionStats

  def __init__(self) -> None:
    # No data structures to initialize
    pass

  def setSolveMethod(self, methodStr: str) -> None:
    # Interpret the method
    solveMethod: SolveMethod = None
    try:
      solveMethod = SolveMethod.Interpret(methodStr)
    except:
      validSolveMethods = SolveMethod.getKeys()
      print(f"Solve method '{methodStr}' is not a valid input. Choose one of the following instead: " + ", ".join(validSolveMethods))
      return

    # Change one or more other params
    if solveMethod == SolveMethod.DFR:
      self.shuffleMoves = True
      self.findSolutionCount = DFR_DEFAULT_SEARCH_ATTEMPTS
    else:
      self.findSolutionCount = 1

    self._solveMethod = solveMethod
    if not self.silentSuccess: print("Set solve method to " + solveMethod.name)
  def getStats(self) -> tuple[SolveStats, SolutionStats]:
    return (self.solveStats, self.lastSolutionStats)

  # Solve method hooks for major events
  def onStartSolve(self, game: Game) -> None:
    self.REPORT_ITERATION_FREQ = 10000 if self._solveMethod == SolveMethod.BFS else 1000
    self.QUEUE_CHECK_FREQ = self.REPORT_ITERATION_FREQ * 10
    pass
  def onNewSolution(self, solution: Game) -> None:
    pass
  def onNextIteration(self, current: Game, numIterations: int) -> None:
    if numIterations % self.REPORT_ITERATION_FREQ != 0:
      return

    if self._solveMethod != SolveMethod.BFS and self._solveMethod != SolveMethod.DFR:
      print(f"Checked {numIterations} iterations.")

    # Check to switch away from BFS in the MIX method
    if self._solveMethod == SolveMethod.MIX and self.searchBFS and current._numMoves >= self.MIX_SWITCH_THRESHOLD_MOVES:
      self.searchBFS = False
      print("Switching to DFS search for MIX solve method")
    elif numIterations % self.QUEUE_CHECK_FREQ == 0:
      if ENABLE_QUEUE_CHECKS and not self.searchBFS:
        self._confirmContinuedOperations(current)
      else:
        self._printQueueCheck(current)
        if self._solveMethod == SolveMethod.MIX:
          self._confirmContinuedOperations(current)
        # Else: We're searching BFS. Don't verify.
    pass
  def _printQueueCheck(self, current: Game) -> None:
    sv, st = self.getStats()
    minsSolving = round((time() - self.solutionStartTime) / 60, 1)
    print(  f"QUEUE CHECK:"
          + f"\t resets: {sv.numResets}"
          + f"\t itrs: {st.numIterations}"
          + f"\t mvs: {current._numMoves}"
          + f"\t q len: {len(st.q)}"
          + f"\t ends: {st.numDeadEnds}"
          + f"\t dup games: {st.numDuplicateGames}"
          + f"\t mins: {minsSolving}")
  def _confirmContinuedOperations(self, current: Game) -> None:
    attemptMixSwitch = self._solveMethod == SolveMethod.MIX and self.searchBFS

    prompt = "This is a lot. Are you sure?"
    if attemptMixSwitch:
      prompt = "This is a lot. Would you like to switch to a faster approach? (Yes/no)"

    rsp = current.requestVal(current, prompt, printState=False)

    if attemptMixSwitch:
      rsp.lower()
      if rsp and rsp[0] == "y":
        self.searchBFS = False
        # self._solveMethod = SolveMethod.DFS
      else:
        # Don't change the BFS settings
        pass

    pass
  def onEndSolve(self) -> None:
    self.printSolveStats()
    if game.level:
      saveGame(game)

    pass
  def _printSolveStats(self) -> None:
    sv, st = self.getStats()

    secsSearching, minsSearching = getTimeRunning(st.startTime, st.endTime)

    print(f"""
          Finished search algorithm:

            Overall:
            {self._solveMethod            }\t   Solving method
            {sv.numResets                 }\t   Num resets
            {sv.minSolution._numMoves if sv.minSolution else "--"}\t   Shortest Solution
            {sv.minSolutionUpdates        }\t   Min solution updates
            {sv.numSolutionsAbandoned     }\t   Num solutions abandoned

            Since last reset:
            {secsSearching                }\t   Seconds searching
            {minsSearching                }\t   Minutes searching
            {st.numIterations             }\t   Num iterations
            {len(st.q)                    }\t   Ending queue length
            {st.maxQueueLength            }\t   Max queue length
            {st.numDeadEnds               }\t   Num dead ends
            {st.numPartialSolutionsGenerated }\t   Partial solutions generated
            {st.numDuplicateGames         }\t   Num duplicate games
            {len(st.computed)             }\t   Num states computed
          """)

    pass
  def _printSolutionReport(self) -> None:
    sv, st = self.getStats()
    if not sv.minSolution:
      print("Cannot not find solution.")
      return

    print("Found solution!")
    sv.minSolution.printMoves()


  def solveGame(self, game: Game):
    # Intelligent search through all the possible game states until we find a solution.
    # The game already handles asking for more information as required

    sv = self.solveStats = SolveStats(
      startTime = time(),
      endTime = None,

      root = game,
      numResets = -1,
      uniqueSolutions = set(),

      minSolution = None,
      allSolutions = list(),
      minSolutionUpdates = 0,
      numSolutionsAbandoned = 0,
    )
    solutionsRemaining = self.findSolutionCount

    self.onStartSolve(game)

    while Game.reset or solutionsRemaining > 0:
      Game.reset = False
      self.solveStats.numResets += 1
      self.onNewSolution()

      # First correct any errors in the game
      game.attemptCorrectErrors()

      self.solutionStartTime = time()

      # Setup our search
      st = self.lastSolutionStats = SolutionStats(
        q = deque(),
        computed = set(),
        solution = None,

        numIterations = 0,
        numDeadEnds = 0,
        numDuplicateGames = 0,
        numPartialSolutionsGenerated = 0,
        maxQueueLength = 1, # Because we added an initial
      )
      st.q.append(game)
      self.searchBFS = self.shouldSearchBFS()

      # Perform the search
      while st.q and not solution:
        # Break out
        if Game.reset or Game.quit:
          break

        # Taking from the front or the back makes all the difference between BFS and DFS
        current = st.q.popleft() if self.searchBFS else st.q.pop()

        # Perform some work at some checkpoints
        st.numIterations += 1
        self.onNextIteration(current, st.numIterations)

        # Prune if we've found a cheaper solution
        if self.solveMethod == SolveMethod.DFR and st.minSolution and st.minSolution._numMoves <= current._numMoves:
          sv.numSolutionsAbandoned += 1
          break # Quit this attempt, and try a different one

        # Check all next moves
        hasNextGame = False
        nextGames = current.generateNextGames()
        if self.shuffleMoves: shuffle(nextGames)
        for nextGame in nextGames:
          st.numPartialSolutionsGenerated += 1
          partialDepth[nextGame._numMoves] += 1

          if nextGame in sv.computed:
            st.numDuplicateGames += 1
            dupGameDepth[nextGame._numMoves] += 1
            continue
          st.computed.add(nextGame)

          hasNextGame = True
          if nextGame.isFinished():
            solution = nextGame
            if not sv.minSolution or solution._numMoves < sv.minSolution._numMoves:
              sv.minSolution = solution
              sv.minSolutionUpdates += 1

            self.onNewSolution(solution)
            break # Finish searching
          else:
            st.q.append(nextGame)

        # Maintain stats
        maxQueueLength = max(maxQueueLength, len(q))
        if not hasNextGame:
          numDeadEnds += 1
          deadEndDepth[current._numMoves] += 1

    # End timer
    self.solveEndTime = time()
    self.onEndSolve()
  def shouldSearchBFS(self) -> bool:
    if self.solveMethod == SolveMethod.BFS or self.solveMethod == SolveMethod.MIX:
      return True
    elif self.solveMethod == SolveMethod.DFS or self.solveMethod == SolveMethod.DFR:
      return False
    else:
      raise Exception("Unrecognized solve method: " + self.solveMethod.name)

