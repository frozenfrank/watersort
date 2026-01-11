from colorama import Fore, Back
from colorama.ansi import AnsiStyle
from collections import defaultdict


#### Months ####

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
MONTH_ABBRS = [month[0:3].lower() for month in MONTHS]


#### Colors & Styles ####

class AnsiConsole(AnsiStyle):
  ITALICS = 3
  UNDERSCORE = 4
  INVERSE = 7
  CONCEALED = 8
  STRIKETHROUGH = 9

Style = AnsiConsole()


RESERVED_COLORS = set(["?", "-"])

def ANSI_FORE(r: int, g: int, b: int) -> str:
  return f"\x1b[38;2;{r};{g};{b}m"
def ANSI_BACK(r: int, g: int, b: int) -> str:
  return f"\x1b[48;2;{r};{g};{b}m"

COLOR_CODES = defaultdict(str, {
  "bl": Back.BLACK + Fore.LIGHTWHITE_EX,          # Black (system)
  "er": Style.BRIGHT + Fore.RED,                  # Error (system)
  "wn": Style.BRIGHT + Fore.YELLOW,               # Warning (system)
  "bold": Style.BRIGHT,                           # Bold (system)

  # The actual color from the game as the background. An HSL inverted color to 20/80% Luminosity
  "m": ANSI_BACK(98, 214, 124) + ANSI_FORE(21, 81, 34),       # Mint
  "g": ANSI_BACK(99, 100, 101) + ANSI_FORE(203, 204, 205),    # Gray
  "o": ANSI_BACK(232, 140, 66) + ANSI_FORE(91, 47, 11),       # Orange
  "y": ANSI_BACK(241, 218, 89) + ANSI_FORE(94, 81, 8),        # Yellow
  "r": ANSI_BACK(197, 42, 35) + ANSI_FORE(87, 19, 15),        # Red
  "p": ANSI_BACK(115, 42, 147) + ANSI_FORE(215, 176, 232),    # Purple
  "pk": ANSI_BACK(120, 150, 15) + ANSI_FORE(228, 246, 162),   # Puke
  "pn": ANSI_BACK(234, 94, 123) + ANSI_FORE(90, 12, 27),      # Pink
  "br": ANSI_BACK(126, 73, 7) + ANSI_FORE(250, 209, 158),     # Brown
  "lb": ANSI_BACK(84, 163, 228) + ANSI_FORE(14, 55, 88),      # Light Blue
  "gn": ANSI_BACK(17, 101, 51) + ANSI_FORE(124, 233, 168),    # Dark Green
  "b": ANSI_BACK(58, 46, 195) + ANSI_FORE(197, 193, 240),     # Blue
})

COLOR_FOREGROUND = defaultdict(str, {
  "m": ANSI_FORE(98, 214, 124),                   # Mint
  "g": ANSI_FORE(99, 100, 101),                   # Gray
  "o": ANSI_FORE(232, 140, 66),                   # Orange
  "y": ANSI_FORE(241, 218, 89),                   # Yellow
  "r": ANSI_FORE(197, 42, 35),                    # Red
  "p": ANSI_FORE(115, 42, 147),                   # Purple
  "pk": ANSI_FORE(120, 150, 15),                  # Puke
  "pn": ANSI_FORE(234, 94, 123),                  # Pink
  "br": ANSI_FORE(126, 73, 7),                    # Brown
  "lb": ANSI_FORE(84, 163, 228),                  # Light Blue
  "gn": ANSI_FORE(17, 101, 51),                   # Dark Green
  "b": ANSI_FORE(58, 46, 195),                    # Blue
})

COLOR_NAMES = defaultdict(lambda: "Unrecognized", {
  "bl": "Black",
  "m": "Mint",
  "g": "Gray",
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


#### Big Characters ####

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
