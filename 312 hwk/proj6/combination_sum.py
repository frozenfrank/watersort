class Solution:
    def combinationSum(self, candidates: list[int], target: int) -> list[list[int]]:
        result = [] # list of answers
        combos = [] # (remaining, list_of_combos)[]

        for index, c in enumerate(candidates):
            # Create entries for every amount of this number
            numReps = 1
            t = c
            while t < target:
                combos.append((target - t, [index] * numReps))
                t += c
                numReps += 1

            # Add our selves to every existing entry, if possible
            i = 0
            while i < len(combos):
                remaining, indices = combos[i]
                newIndices = [index]
                while remaining >= c:
                    if remaining == c:
                        indices.extend(newIndices)
                        result.append(indices)
                        del combos[i]
                        i -= 1
                        break
                    else:
                        remaining -= c
                        newIndices.append(index)
                        combos.insert(i, (remaining, newIndices.copy()))
                        i += 1
                i += 1

        return result

def test(candidates: list[int], target: int, ans: list[list[int]]) -> bool:
    solve = Solution()
    rsp = solve.combinationSum(candidates, target)
    print("Expected: \t" + str(ans))
    print("Received: \t" + str(rsp))
    correct = True
    # correct = set(rsp) == set(ans)
    # print("Correct!" if correct else f"Incorrect! ({rsp})")
    return correct

def tests():
    test([2,3,6,7], 7, [[2,2,3],[7]])
    test([2,3,5], 8, [[2,2,2,2],[2,3,3],[3,5]])
    test([2], 1, [])

tests()

