nq = int(input())
ans = input()

seq = [
  "ABC",
  "BABC",
  "CCAABB"
]
cor = [0] * len(seq)
player = [
  "Adrian",
  "Bruno",
  "Goran"
]

i = 0
while i < len(ans):
  for p in range(len(seq)):
    if seq[p][i % len(seq[p])] == ans[i]:
      cor[p] += 1
  i += 1

mx = max(cor)
print(mx)
for p, score in zip(player, cor):
  if score == mx:
    print(p)
