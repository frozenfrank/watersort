read = lambda:sorted(map(int, input().split()))

while(True):
  a,b,c = read()
  if a + b + c == 0:
    break
  if a**2 + b**2 == c**2:
    print("right")
  else:
    print("wrong")

