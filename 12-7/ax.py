while True:
  n = int(input())
  if n == -1:
    break

  d = 0
  lt = 0
  for _ in range(n):
    s, t = map(int, input().split())
    d += s * (t - lt)
    lt = t

  print(f"{d} miles")
