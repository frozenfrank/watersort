class Solution:
    def findCircleNum(self, isConnected: list[list[int]]) -> int:
        numProvinces = 0
        n = len(isConnected)
        unvisited = set(range(n))
        q = []

        # Count the number of forests in our DFS forest
        while unvisited:
            numProvinces += 1
            q.append(unvisited.pop())

            # DFS to mark all connected cities as visited
            while q:
                currentIndex = q.pop()
                for otherIndex, otherConnected in enumerate(isConnected[currentIndex]):
                    if otherConnected == 1 and otherIndex in unvisited:
                        if currentIndex != otherIndex:
                            q.append(otherIndex)
                        unvisited.remove(otherIndex)

        return numProvinces

def test(isConnected: list[list[int]], ans: int) -> bool:
    solve = Solution()
    rsp = solve.findCircleNum(isConnected)
    correct = rsp == ans
    print("Correct!" if correct else f"Incorrect ({rsp})")
    return correct

def tests():
    test([[1,1,0],[1,1,0],[0,0,1]], 2)
    test([[1,0,0],[0,1,0],[0,0,1]], 3)

tests()
