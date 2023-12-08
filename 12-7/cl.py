n = int(input())
l = []
for _ in range(n):
  i1, i2 = input().split()
  l.append((int(i1), i2) if i1.isnumeric() else (int(i2) * 2, i1))

for count, color in sorted(l):
  print(color)
