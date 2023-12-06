maxGuess = 1000
minGuess = 1

while True:
  nextGuess = (minGuess + maxGuess) // 2
  print(nextGuess, flush=True)
  response = input()
  if response == "lower":
    maxGuess = nextGuess - 1
  elif response == "higher":
    minGuess = nextGuess + 1
  else:
    break; # Success!