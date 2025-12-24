from colorama import Fore, Back
from collections import   defaultdict

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

class BigDigit:
  _width: int
  _height = 7
  _lines: str

  @staticmethod
  def FormatSingleLine(*digits: list["BigDigit"], spacing = 2) -> list[str]:
    separator = " " * spacing
    resultLines = [""] * BigDigit._height
    for i in range(BigDigit._height):
      resultLines[i] += separator.join(map(lambda digit: digit._lines[i], digits))
    return resultLines


  def __init__(self, chars: str, width = None):
    lines = chars.split("\n")
    if len(lines)==9:
      del lines[8]
      del lines[0]
    if len(lines) != self._height:
      raise ValueError("BigDigit must be initialized with exactly 7 lines")

    self._width = width if width else max(map(lambda line: len(line), lines))
    self._lines = list(map(lambda line: line.ljust(self._width), lines))

  def __str__(self):
    return "\n".join(self._lines)

BIG_DIGITS = list(map(BigDigit, [
"""
#######
##   ##
##   ##
##   ##
##   ##
##   ##
#######
""",
"""
   ##
  ###
 ####
   ##
   ##
   ##
 #####
""",
"""
######
     ##
     ##
 #####
##
##
######
""",
"""
######
     ##
     ##
  #####
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
  #####
 ##
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

LEFT_ARROW = BigDigit("""

           @
           @@
@@@@@@@@@@@@@@
           @@
           @

""")

print("\n".join(BigDigit.FormatSingleLine(BIG_DIGITS[9],BIG_DIGITS[7],LEFT_ARROW,BIG_DIGITS[8],spacing=3)))
print("\n".join(BigDigit.FormatSingleLine(*[BIG_DIGITS[9],BIG_DIGITS[7],LEFT_ARROW,BIG_DIGITS[8]],spacing=3)))
print(" hello ".center(50,"-"))
