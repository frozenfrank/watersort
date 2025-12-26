from colorama import Fore, Back
from collections import defaultdict

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
MONTH_ABBRS = [month[0:3].lower() for month in MONTHS]

RESERVED_COLORS = set(["?", "-"])

COLOR_CODES = defaultdict(str, {
  "m": Back.CYAN,                                 # Mint
  "g": Back.LIGHTBLACK_EX + Fore.WHITE,           # Gray
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

COLOR_NAMES = defaultdict(lambda: "Unrecognized", {
  "m": "Mint",
  "g": "Gray",
  "gr": "Green",
  "o": "Orange",
  "y": "Yellow",
  "r": "Red",
  "p": "Purple",
  "pk": "Puke",
  "pn": "Pink",
  "br": "Brown",
  "lb": "Blue",
  "gn": "Green",
  "b": "Blue",
  "?": "Unknown",
  "-": "Empty",
})

class BigChar:
  _width: int
  _height = 7
  _lines: str


  @staticmethod
  def FromNumber(number: int) -> list["BigChar"]:
    return list(map(lambda char: BIG_DIGITS[int(char)], str(number)))

  @staticmethod
  def FromSymbols(symbols: str) -> list["BigChar"]:
    return list(map(lambda char: BIG_SYMBOLS[char], symbols))

  @staticmethod
  def FormatSingleLine(*digits: list["BigChar"], spacing = 3) -> list[str]:
    separator = " " * spacing
    resultLines = [""] * BigChar._height
    for i in range(BigChar._height):
      resultLines[i] += separator.join(map(lambda digit: digit._lines[i], digits))
    return resultLines

  @staticmethod
  def PrintSymbols(symbols: str) -> None:
    bigChars = BigChar.FromSymbols(symbols)
    lines = ["\n", *BigChar.FormatSingleLine(*bigChars)]
    print("\n".join(lines))


  def __init__(self, chars: str, width = None):
    lines = chars.split("\n")
    if len(lines)==9:
      del lines[8]
      del lines[0]
    if len(lines) != self._height:
      raise ValueError("BigChar must be initialized with exactly 7 lines")

    self._width = width if width else max(map(lambda line: len(line), lines))
    self._lines = list(map(lambda line: line.ljust(self._width), lines))

  def __str__(self):
    return "\n".join(self._lines)

BIG_DIGITS = list(map(BigChar, [
"""
 #####
##   ##
##   ##
##   ##
##   ##
##   ##
 #####
""",
"""
   ##
  ###
 ####
   ##
   ##
   ##
 ######
""",
"""
 #####
#    ##
     ##
 #####
##
##
#######
""",
"""
######
     ##
     ##
  ####
     ##
     ##
######
""",
"""
##   ##
##   ##
##   ##
 ######
     ##
     ##
     ##
""",
"""
#######
##
##
######
     ##
     ##
######
""",
"""
  ####
 ##   #
##
######
##   ##
##   ##
 #####
""",
"""
#######
     ##
     ##
    ##
   ##
   ##
   ##
""",
"""
 #####
##   ##
##   ##
 #####
##   ##
##   ##
 #####
""",
"""
 #####
##   ##
##   ##
 ######
     ##
    ##
  ##
""",
]))

def parseCharText(text: str) -> tuple[str, "BigChar"]:
  return text[0], BigChar(text[1:])
BIG_SYMBOLS = defaultdict(lambda: BIG_SYMBOLS["□"], map(parseCharText, [
# cdeinorstu
"""C
  ####
 ##  ##
##
##
##
 ##  ##
  ####
""",
"""D
#####
##   ##
##     ##
##     ##
##     ##
##   ##
#####
""",
"""E
#######
##
##
####
##
##
#######
""",
"""I
########
   ##
   ##
   ##
   ##
   ##
########
""",
"""N
##    ##
###   ##
####  ##
## ## ##
##  ####
##   ###
##    ##
""",
"""O
   ###
 ##   ##
##     ##
##     ##
##     ##
 ##   ##
   ###
""",
"""R
######
##   ##
##   ##
#####
##  ##
##   ##
##    ##
""",
"""S
  ####
##    ##
 ##
   ##
     ##
##    ##
  ####
""",
"""T
##########
    ##
    ##
    ##
    ##
    ##
    ##
""",
"""U
##     ##
##     ##
##     ##
##     ##
##     ##
 ##   ##
  #####
""",
"""→

           @
           @@
@@@@@@@@@@@@@@
           @@
           @

""",
""".





##
##
""",
"""□

┌─────┐
│     │
│  ╳  │
│     │
└─────┘

""",
]))

# Populate BIG_SYMBOLS with digit mappings
for digit in range(10):
  BIG_SYMBOLS[       digit ]=BIG_DIGITS[digit]
  BIG_SYMBOLS[""+str(digit)]=BIG_DIGITS[digit]
