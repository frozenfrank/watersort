from watersort2.game import Game


class GamePlayer:
  base: "Game"

  @staticmethod
  def Play(base: "Game") -> None:
    player = GamePlayer(base)
    player.play()

  def __init__(self, base: "Game") -> None:
    self.base = base

  def play(self) -> None:
    if not self.base:
      raise TypeError("No game to play")

    currentGame = self.base
    print("""
          Play the game:
          r         reset
          q         quit
          NUM NUM   move from vial to vial
          """)
    while True:
      currentGame.printMoves()
      currentGame.printVials()
      read = input()
      if not read:
        continue
      elif read == "q":
        break
      elif read == "r":
        currentGame = self.base
        continue
      read1, read2 = read.split()

      startVial, endVial = int(read1) - 1, int(read2) - 1
      if not currentGame.canMove(startVial, endVial):
        print("That move is invalid")
        continue

      # Perform the move
      currentGame = currentGame.spawn((startVial, endVial))

    print("Goodbye.")
