n = int(input())

isOdd = True
while n:
  n -= 1
  word = input()
  if isOdd:
    print(word)
  isOdd = not isOdd