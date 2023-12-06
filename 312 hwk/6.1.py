from sys import stdin
from collections import deque

def max_contiguous_subsequence(arr: list[float]) -> list[float]:
  # Initialize arrays
  max   = []
  prev  = []

  # Calculate the max sequence array
  sum = float("-inf")
  usePrev: bool = None
  maxValue = float("-inf")
  maxIndex: int = None
  for i in range(len(arr)):
    num = arr[i]

    # Make decision
    if sum > 0:
      usePrev = True
      sum += num
    else:
      usePrev = False
      sum = num

    # Store decision
    max.append(sum)
    prev.append(usePrev)

    if sum > maxValue:
      maxIndex = i
      maxValue = sum

  # Reconstruct the subsequence
  subsequence = deque()
  subsequence.append(arr[maxIndex])
  while prev[maxIndex]:
    maxIndex -= 1
    subsequence.appendleft(arr[maxIndex])

  # The numbers making up the subsequence with maximum sum
  return list(subsequence)

# Run the algorithm on multiple test cases, each test case occupying a single line
# until an empty line signals to stop
for line in stdin:
  line = line.strip()
  if not line or line == '':
    break

  nums = list(map(int, line.split()))
  maxSubsequence = max_contiguous_subsequence(nums)
  print(f"Input:    {nums}")
  print(f"Max Sub:  {maxSubsequence}")
  print(f"Sum:      {sum(maxSubsequence)}")
  print("")

print("Done.")

