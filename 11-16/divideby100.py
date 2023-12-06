from collections import deque

n = deque(input().strip())
m = input().strip()

i = (len(m) - 1) * -1
if i != 0:
  if len(m) > len(n):
    for _ in range(len(m) - len(n)):
      n.insert(0, '0')

  n.insert(i, '.')

  # Remove trailing zeros
  for j in range(len(n) - 1, i - 1, -1):
    if n[j] == '0':
      n.pop()
    else:
      break
  if n[-1] == '.':
    n.pop()

  # Add leading zero
  if n[0] == '.':
    n.insert(0, '0')

  # while n[0] == '0' and n[1] != '.':
  #   del n[0]

print(''.join(n))
