class Solution:
    def gardenNoAdj(self, n: int, paths: list[list[int]]) -> list[int]:
        colors = [0] * n

        # Populate edges
        neighbors = tuple(list() for _ in range(n))
        for s, t in paths:
            if s > t:
                neighbors[s-1].append(t-1)
            else:
                neighbors[t-1].append(s-1)


        # Identify all bordering colors
        for garden in range(n):
            nColors = {1,2,3,4}
            for neighbor in neighbors[garden]:
                if colors[neighbor] in nColors:
                    nColors.remove(colors[neighbor])

            colors[garden] = nColors.pop()

        return colors


def test(n: int, paths: list[list[int]], ans: int) -> bool:
    solve = Solution()
    rsp = solve.gardenNoAdj(n, paths)
    correct = rsp == ans
    print("Correct!" if correct else rsp)
    return correct

def tests():
    test(3, [[1,2],[2,3],[3,1]], [1,2,3])
    test(4, [[1,2],[3,4]], [1,2,1,2])
    test(4, [[1,2],[2,3],[3,4],[4,1],[1,3],[2,4]], [1,2,3,4])

tests()