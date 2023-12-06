from collections import *

r,c = map(int, input().split())
g = [list(input()) for _ in range(r)]

a = 0
def dfs(x, y):
  if x < 0 or x >= r or y < 0 or y >= c:
    return

  v = g[x][y]
  g[x][y] = "V"

  if v == "#":
    dfs(x-1, y-1)
    dfs(x+0, y-1)
    dfs(x+1, y-1)

    dfs(x-1, y+0)
    dfs(x+1, y+0)

    dfs(x-1, y+1)
    dfs(x+0, y+1)
    dfs(x+1, y+1)


q = deque()
for x in range(r):
  for y in range(c):
    if g[x][y] == "#":
      q.append((x,y))

while q:
  x,y = q.popleft()
  if g[x][y] == "V":
    continue
  a += 1
  dfs(x, y)

print(a)
