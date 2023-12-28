from collections import defaultdict
from time import time
from personal.watersort.game import Game
from personal.watersort.solver_base import SolveMethod, Solver


class AnalyzerSolver(Solver):

  REPORT_SEC_FREQ = 15

  # ... A whole host of params initialized in `onStartSolve()`

  def __init__(self) -> None:
    super().__init__()

  # Override several solutions hooks
  def onStartSolve(self, game: Game) -> None:
    self.analysisStart: float = time()
    self.partialDepth = defaultdict(int)
    self.dupGameDepth = defaultdict(int)
    self.deadEndDepth = defaultdict(int)
    self.solutionDepth = defaultdict(int)
    self.uniqueSolsDepth = defaultdict(int)
    self.solFindSeconds = defaultdict(int)
    self.uniqueSolutions: set["Game"] = set()
    self.isUniqueList: list[bool] = list()
    self.lastReportTime = 0
    return super().onStartSolve(game)
  def onNewSolution(self, solutionsRemaining: int):
    timeCheck = time()
    if solutionsRemaining % 1000 == 0 or timeCheck - lastReportTime > self.REPORT_SEC_FREQ:
      print(f"Searching for {solutionsRemaining} more solutions. Running for {round(timeCheck - self.analysisStart, 1)} seconds. ")
      lastReportTime = timeCheck
  def onNextIteration(self, current: Game, numIterations: int) -> None:
    '''Skip the standard checks that occur on each iteration'''
    pass