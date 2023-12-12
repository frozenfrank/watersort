class Solution:
    validNums: list[int]
    adds: list[int]

    def numSquares(self, n: int) -> int:
        # Generate perfect squares up to n
        squares = []
        while True:
            nxtSqr = (len(squares) + 1) ** 2
            if nxtSqr > n: break
            squares.append(nxtSqr)

        # Set up dp arrays
        self.validNums = squares
        self.adds = [None] * (n + 1)
        self.adds[0] = 0

        return self.cheapestAdds(n)
    def cheapestAdds(self, toValue: int) -> int:
        if toValue < 0:
            return float("inf")
        if self.adds[toValue] != None:
            return self.adds[toValue]

        adds = min([(self.cheapestAdds(toValue - value) + 1) for value in self.validNums])
        self.adds[toValue] = adds
        return adds

def test(num: int, ans: int) -> bool:
    solve = Solution()
    rsp = solve.numSquares(num)
    correct = rsp == ans
    print("Correct!" if correct else f"Incorrect! ({rsp})")
    return correct

def tests():
    test(12, 3)
    test(13, 2)

tests()
