from colorama import Fore, Back, Style
from collections import defaultdict

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
MONTH_ABBRS = [month[0:3].lower() for month in MONTHS]

RESERVED_COLORS = set(["?", "-"])

COLOR_CODES = defaultdict(str, {
  "bl": Back.BLACK + Fore.LIGHTWHITE_EX,          # Black (system)
  "er": Style.BRIGHT + Fore.RED,                  # Error (system)

  "m": Back.CYAN,                                 # Mint
  "g": Back.LIGHTBLACK_EX + Fore.LIGHTWHITE_EX,   # Gray
  "gr": "",                                       # Green (Occasionally)
  "o": Back.YELLOW + Fore.RED,                    # Orange
  "y": Back.YELLOW + Fore.BLACK,                  # Yellow
  "r": Back.RED + Fore.LIGHTWHITE_EX,             # Red
  "p": Back.BLACK  + Fore.MAGENTA,                # Purple
  "pk": Back.GREEN + Fore.BLACK,                  # Puke
  "pn": Back.MAGENTA,                             # Pink
  "br": Back.WHITE + Fore.MAGENTA,                # Brown
  "lb": Fore.CYAN + Back.WHITE,                   # Light Blue
  "gn": Back.BLACK + Fore.GREEN,                  # Dark Green
  "b": Back.BLUE + Fore.LIGHTWHITE_EX,            # Blue
  "?": "",                                        # Unknown
  "-": "",                                        # Empty
})

COLOR_NAMES = defaultdict(lambda: "Unrecognized", {
  "bl": "Black",
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
  "lb": "Light Blue",
  "gn": "Green",
  "b": "Blue",
  "?": "Unknown",
  "-": "Empty",
})

class BigChar:
  _width: int
  _height: int
  _lines: str


  @staticmethod
  def FromNumber(number: int) -> list["BigChar"]:
    return list(map(lambda char: BIG_DIGITS[int(char)], str(number)))

  @staticmethod
  def FromSymbols(symbols: str) -> list["BigChar"]:
    return list(map(lambda char: BIG_SYMBOLS[char], symbols))

  @staticmethod
  def FormatSingleLine(*digits: list["BigChar"], spacing = 3) -> list[str]:
    if not digits: return [] # Carefully avoid empty-state crashes
    height = digits[0]._height
    separator = " " * spacing
    resultLines = [""] * height
    for i in range(height):
      resultLines[i] += separator.join(map(lambda digit: digit._lines[i], digits))
    return resultLines

  @staticmethod
  def PrintSymbols(symbols: str) -> None:
    BigChar.PrintChars(BigChar.FromSymbols(symbols))

  @staticmethod
  def PrintChars(chars: list["BigChar"]) -> None:
    lines = ["", *BigChar.FormatSingleLine(*chars), ""]
    print("\n".join(lines))


  def __init__(self, chars: str, width: int = None, height: int = 7):
    lines = chars.split("\n")
    if len(lines)==height+2:
      del lines[0]
      del lines[-1]
    if len(lines) != height:
      raise ValueError(f"BigChar must be initialized with exactly {height} lines")

    self._height = height
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
"""A
   ###
  ## ##
 ##   ##
 #######
 ##   ##
##     ##
##     ##
""",
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
"""L
##
##
##
##
##
##
#######
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
"""P
######
##   ##
##   ##
#####
##
##
##
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
"""?
  ###
##   ##
     ##
   ##
   ##

   ##
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
"""✅
        ​✅
       ​✅
      ​✅
     ​✅
​✅  ​✅
 ​✅​✅
  ​✅
""",
]))

# Populate BIG_SYMBOLS with digit mappings
for digit in range(10):
  BIG_SYMBOLS[       digit ]=BIG_DIGITS[digit]
  BIG_SYMBOLS[""+str(digit)]=BIG_DIGITS[digit]

class BigShades(BigChar):
  Light = "░"
  Medium = "▒"
  Dark = "▓"
  Fill = "█"


  @staticmethod
  def FromShading(shading: str) -> list["BigChar"]:
    return list(map(lambda char: BIG_SHADING[char], shading))

  @staticmethod
  def PrintShades(shading: str) -> None:
    BigChar.PrintChars(BigShades.FromShading(shading))

def constructShadingChar(shading: str) -> BigChar:
  shadingWidth = 4
  line = shading * shadingWidth
  shadingChars = line + "\n" + line
  return shading, BigChar(shadingChars, height=2, width=shadingWidth)
BIG_SHADING = dict(map(constructShadingChar, "█▓▒░"))
