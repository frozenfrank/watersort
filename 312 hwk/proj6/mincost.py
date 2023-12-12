import numpy as np

Point = list[int] # (x, y)
class Solution:
    points: list[Point]
    costsReused: int
    costComputed: int
    _dist: dict[int, int] # (from, to)

    def __init__(self) -> None:
        self.costsReused = 0
        self.costComputed = 0

    def minCostConnectPoints(self, points: list[Point]) -> int:
        numPoints = len(points)
        self.points = points
        mst = set()
        self._dist = dict()
        costTo = np.array([float('inf')] * numPoints)

        currIndex = 0
        mst.add(currIndex)
        minCost = 0
        while len(mst) < numPoints:
            for nextIndex in range(numPoints):
                if nextIndex in mst:
                    continue
                costTo[nextIndex] = min(costTo[nextIndex], self.getCost(currIndex, nextIndex))

            cheapestIndex = np.argmin(costTo)
            # print(f"next: {cheapestIndex}, cost: {costTo[cheapestIndex]}, \tcostTo: {costTo}")
            minCost += costTo[cheapestIndex]
            costTo[cheapestIndex] = float('inf')
            currIndex = cheapestIndex
            mst.add(currIndex)

        # print(self._dist)
        # print(f"Costs computed={self.costComputed}, Costs reused={self.costsReused}")
        return int(minCost)

    def getCost(self, i1: int, i2: int) -> int:
        edge = (i1, i2) if i1 < i2 else (i2, i1)
        if edge in self._dist:
            self.costsReused += 1
            return self._dist[edge]

        self.costComputed += 1
        p1 = self.points[i1]
        p2 = self.points[i2]
        dist = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        self._dist[edge] = dist
        return dist

def test(points: list[Point], ans: int) -> bool:
    solve = Solution()
    rsp = solve.minCostConnectPoints(points)
    correct = rsp == ans
    print("Correct!" if correct else f"Incorrect! ({rsp})")
    return correct

def tests():
    test([[0,0],[2,2],[3,10],[5,2],[7,0]], 20)
    test([[3,12],[-2,5],[-4,1]], 18)

tests()
