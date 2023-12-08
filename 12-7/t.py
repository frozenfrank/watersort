import math

nr = int(input())
radii = list(map(int, input().split()))

nums = []
dens = []

cn = 1
dc = 1
for r in radii[1:]:
  nums.append(radii[0])
  dens.append(r)

for n, d in zip(nums, dens):
  g = math.gcd(n, d) / 1
  n /= g
  d /= g
  print(f"{int(n)}/{int(d)}")
