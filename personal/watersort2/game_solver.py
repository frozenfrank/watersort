from collections import defaultdict, deque
import random
from time import time

from watersort import saveGame
from watersort2.constant import ENABLE_QUEUE_CHECKS, MIX_SWITCH_THRESHOLD_MOVES, VALID_SOLVE_METHODS
from watersort2.game import Game


class GameSolver:

  def solveGame(self, game: "Game", solveMethod = "MIX", analyzeSampleCount = 0, probeDFRSamples = 0):
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
      searchBFS: bool = self.shouldSearchBFS()

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
  def shouldSearchBFS(self) -> bool:
    if SOLVE_METHOD == "BFS" or SOLVE_METHOD == "MIX":
      return True
    elif SOLVE_METHOD == "DFS" or SOLVE_METHOD == "DFR":
      return False
    else:
      raise Exception("Unrecognized solve method: " + SOLVE_METHOD)
    
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

  def setSolveMethod(self, method: str) -> bool:
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
