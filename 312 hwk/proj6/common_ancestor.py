# Definition for a binary tree node.
class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

NodePath = list[tuple[int, 'TreeNode']] # (leftDirectionToNext, node)[]
class Solution:
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode', q: 'TreeNode') -> 'TreeNode':
        pathToP = self.pathToNode(root, p)
        pathToQ = self.pathToNode(root, q)

        lowest: TreeNode = None
        for pStep, qStep in zip(pathToP, pathToQ):
            lowest = pStep[1]
            if pStep[0] != qStep[0]:
                break

        return lowest

    # Returns the path to the node, including the root node and the discovered node at the bottom
    # The discovered node has None as the direction value
    def pathToNode(self, root: 'TreeNode', node: 'TreeNode') -> NodePath:
        path = list() # (left, node)[]
        path.append((None, root))

        # Indicates the action to perform next time it's visited
        # 0 = Check left
        # 1 = Check right
        # 2 = Backtrack
        states = {}

        while path:
            left, curr = path[-1]

            key = curr.val
            if key not in states:
                states[key] = 1
                if curr.val == node.val:
                    path[-1] = (None, curr) # We found it
                    return path
                elif curr.left:
                    path[-1] = (True, curr) # Exploring left
                    path.append((None, curr.left))
                    continue
            if states[key] == 1:
                states[key] = 2
                if curr.right:
                    path[-1] = (False, curr) # Exploring right
                    path.append((None, curr.right))
                    continue
            if states[key] == 2:
                del states[key]
                path.pop()
                continue

        # We're guaranteed to find the value in the tree

    def stringifyPath(self, path: NodePath) -> None:
        res = list()
        for nextDirection, node in path:
            word = "arrived"
            if nextDirection != None:
                word = "left" if nextDirection else "right"
            res.append(f"{node.val} ({word})")
        return "\n".join(res)

def test(l: list[int], p: int, q: int, ans: int) -> bool:
    solve = Solution()

    # Convert to TreeNode's
    n = [TreeNode(v) for v in l]
    pNode: TreeNode
    qNode: TreeNode
    for i in range(len(l)):
        if      l[i] == p:  pNode = n[i]
        elif    l[i] == q:  qNode = n[i]
        lIndex = 2*i + 1
        rIndex = 2*i + 2
        if lIndex < len(n):
            n[i].left = n[lIndex] if l[lIndex] != None else None
            if rIndex < len(n):
                n[i].right = n[rIndex] if l[rIndex] != None else None

    # Solve
    resultNode = solve.lowestCommonAncestor(n[0], pNode, qNode)
    result = resultNode.val if resultNode else None

    # Return
    correct = result == ans
    print("Correct!" if correct else "Incorrect :(")
    return correct

def tests():
    test([3,5,1,6,2,0,8,None,None,7,4], 5, 1, 3)
    test([3,5,1,6,2,0,8,None,None,7,4], 5, 4, 5)
    test([1,2], 1, 2, 1)
    test([3,5,1,6,2,0,8,None,None,7,4], 0, 8, 1)

tests()
