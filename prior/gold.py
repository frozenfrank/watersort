from collections import *

w, h = map(int, input().split())
g = [input() for _ in range(h)]

q = deque()
for i in range(h):
  for j in range(w):
    if g[i][j] == "P":
      q.append((i, j))


dirs = [1, 0, -1, 0, 1]
def n(i, j):
  p = []
  for k,l in zip(dirs, dirs[1:]):
    x,y = i+k, l+j
    if g[x][y]=="T":
      return []
    elif g[x][y] != "#":
      p.append((x,y))
  return p

v=set()
o = 0
while q:
  i,j = q.popleft()
  if (i,j) in v:
    continue
  v.add((i,j))

  t = g[i][j]
  if t=="G":
    o += 1
  elif t=="#":
    continue

  for (x,y) in n(i,j):
    q.append((x,y))

print(o)
