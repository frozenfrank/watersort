import sys

for line in sys.stdin:
  values = list(map(int, line.split()))
  if not len(values):
    break # End of file

  sumValues = sum(values)
  for value in values:
    if value == sumValues - value:
      print(value)
      break
