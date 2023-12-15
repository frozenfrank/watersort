import sys

sum = 0
num = int(sys.argv[1])
for i in range(num):
  sum += i
print(sum, num ** 2)
