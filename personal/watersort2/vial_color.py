
from collections import defaultdict

from colorama import Back, Fore, Style


COLOR_CODES = defaultdict(str, {
  "m": Back.CYAN,                                 # Mint
  "g": Style.DIM + Back.WHITE,                    # Gray
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


def formatVialColor(color: str, text: str = "", ljust=0) -> str:
  """Formats a color for printing. If text is provided, it will autoreset the style afterwards as well."""
  out = COLOR_CODES[color]
  if text:
    out += text + Style.RESET_ALL
    out += " " * (ljust - len(text))
  return out
