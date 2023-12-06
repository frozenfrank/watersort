import math

p = [list(map(int, input().split())) for i in range(3)]
a = [None] * 10 # [None, (row, col) * 9]
for i in range(3):
  for j in range(3):
    v = p[i][j]
    a[v] = (i, j)

d = 0
for i in range(8):
  p1 = a[i + 1]
  p2 = a[i + 2]
  d += math.sqrt((p1[0] - p2[0]) ** 2 + ((p1[1] - p2[1]) ** 2))

print(d)
