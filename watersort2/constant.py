
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

RESERVED_COLORS = set(["?", "-"])
