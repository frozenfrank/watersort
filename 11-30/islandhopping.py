import math

n = int(input())

def parent(p, i):
  if p[i] == i: return i
  p[i] = parent(p, p[i])
  return p[i]


for _ in range(n):
  m = int(input()) # num islands
  c = list() # costs
  e = list() # edges (distance, i, j)
  p = list() # parent

  for i in range(m):
    x, y = map(float, input().split())
    c.append((x, y))
    p.append(i)

  for i in range(m):
    for j in range(i+1, m):
      xi, yi = c[i]
      xj, yj = c[j]
      d = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
      e.append((d, i, j))

  e.sort(reverse=True)

  t = 0
  a = m-1
  while e and a:
    d, i, j = e.pop()
    if parent(p, i) == parent(p, j):
      continue
    t += d
    a -= 1
    p[p[i]] = p[j] # merge parent

  print(t)
