global f
f = [0, 1]
def fact(n):
  if n < len(f):
    return f[n]

  while len(f) - 1 < n:
    f.append(f[-1] * len(f))

  return f[n]

fact(5)
print(f)
fact(10)
print(f)

while False:
  n = int(input())
  if n == 0:
    break

  year = n
  bitsYear = 2 ** ((year - 1960) // 10 + 2)
  maxVal = 2 ** bitsYear

  i = 1
  while fact(i) < maxVal:
    i += 1

  print(i-1)
