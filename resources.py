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
