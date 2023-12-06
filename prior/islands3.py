from collections import *

r,c=map(int, input().split())
g=[list(input()) for _ in range(r)]

def dfs(x,y):
  if x < 0 or x >= r or y < 0 or y >= c:
    return

  v = g[x][y]
  g[x][y] = "V" # Visited
  if v == "W" or v == "V":
    return

  dfs(x+0, y+1)
  dfs(x+0, y-1)
  dfs(x+1, y+0)
  dfs(x-1, y+0)

l = 0
q = deque()
for x in range(r):
  for y in range(c):
    if g[x][y] == "L":
      q.append((x,y))


while q:
  x,y = q.popleft()
  if g[x][y] == "V":
    continue
  l += 1
  dfs(x,y)


print(l)
