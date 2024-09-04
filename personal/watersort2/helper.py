
def fPercent(num: float, den: float, roundDigits=1) -> str:
  if den == 0: return "--%"
  return str(round(num/den*100, roundDigits)) + "%"
def getTimeRunning(startTime: float, endTime: float) -> tuple[float, float]:
  '''(seconds, minutes), a tuple of printable number representing the time elapsed'''
  seconds = round(endTime - startTime, 1)
  minutes = round((endTime - startTime) / 60, 1)
  return (seconds, minutes)
