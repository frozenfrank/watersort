n = map(int, list(input()))
while True:
  p = 1
  for d in n:
    if d != 0:
      p *= d

  if p < 10:
    print(p)
    break
  else:
    n = map(int, list(str(p)))
