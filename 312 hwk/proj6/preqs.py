import collections

class Solution:
    visited: set[int]
    deps: collections.defaultdict[list[int]] # start: [courses that follow]
    foundBackEdge: bool


    def canFinish(self, numCourses: int, prerequisites: list[list[int]]) -> bool:
        sources = set(range(numCourses))
        self.deps = collections.defaultdict(list)
        self.visited = [0] * numCourses
        self.foundBackEdge = False

        # Process prereqs
        for a, b in prerequisites:
            if a == b:
                return False # It's a self-loop, a subset of SCC's
            if a in sources:
                sources.remove(a)
            self.deps[b].append(a)

        # Early exit condition
        if not len(sources):
            # Impossible to start the degree
            return False

        # Verify each source has a linear path to the end
        for source in sources:
            self.dfsUtil(source)
            if self.foundBackEdge:
                return False

        # Detect unvisited nodes
        # These indicate a SCC wasn't discovered at all
        for visited in self.visited:
            if not visited:
                return False

        # This is the most definitive answer
        return True

    def dfsUtil(self, node: int) -> bool: # Returns a bool indicating if we found back edge
        if self.foundBackEdge:
            return # Break out early

        self.visited[node] = True
        self.startTime[node] = self.clock
        self.clock += 1

        foundBackEdge = False
        for neighbor in self.deps[node]:
            if not self.visited[neighbor]:
                foundBackEdge = self.dfsUtil(neighbor)
                if foundBackEdge:
                    return True
            else:
                # Detect a back edge in the graph
                # Occurs when the neighbor has already been visited
                # if self.startTime[node] > self.startTime[neighbor] and not self.endTime[neighbor]:
                if not self.endTime[neighbor]:
                    self.foundBackEdge = True
                    return True

        self.endTime[node] = self.clock
        self.clock += 1
        return False

def test(numCourses: int, prereqs: list[list[int]], ans: bool) -> bool:
    solve = Solution()
    rsp = solve.canFinish(numCourses, prereqs)
    correct = rsp == ans
    print("Correct!" if correct else f"Incorrect! ({rsp})")
    return correct

def tests():
    test(2, [[1,0]], True)
    test(2, [[1,0],[0,1]], False)
    test(20, [[0,10],[3,18],[5,5],[6,11],[11,14],[13,1],[15,1],[17,4]], False)

    test(5, [[2, 1], [3,2], [4,3], [2,4]], False)

tests()
