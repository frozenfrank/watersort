class Solution:
    inf = float("inf")

    def minimumTotal(self, triangle: list[list[int]]) -> int:

        data: list[list[int]] = [list(), None]              # The current row, and the next row
        data[0].append(triangle[0][0])                      # Init first row explicitly
        # print(data[0])

        # Fill out the row after us
        rowIndex = 0
        while rowIndex < len(triangle) - 1:
            # Select rows carefully
            cdRow = data[0]                                         # Current data row
            ndRow = data[1] = [Solution.inf] * (rowIndex + 2)       # Next data row
            ntRow = triangle[rowIndex + 1]                          # Next triangle row

            # Perform dynamic programming projection into next row
            ndRow[0] = cdRow[0] + ntRow[0] # Only the first value will be fill in by this edge
            for c in range(rowIndex + 1):
                ndRow[c + 1]    = cdRow[c] + ntRow[c+1]         # Project the value into the right side
                ndRow[c]  = min(ndRow[c], cdRow[c] + ntRow[c])  # Choose the min of the projected value, or our new one

            # print(ndRow)
            data.reverse()
            rowIndex += 1

        # Return solution
        return min(data[0])


def test(triangle: list[list[int]], ans: int) -> bool:
    sol = Solution()

    if sol.minimumTotal(triangle) == ans:
        print("Correct!")
        return True
    else:
        print("Incorrect")
        return False
def tests():
    test1()
    test2()

def test1():
    test([[2],[3,4],[6,5,7],[4,1,8,3]], 11)
def test2():
    test([[-10]], -10)

tests()