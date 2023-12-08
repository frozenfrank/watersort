nd = int(input())
p = [map(int, input().split()) for _ in range(3)]

o = []
for a in zip(p[0], p[1], p[2]):
  o.append(sorted(a)[1])

print(*o)
