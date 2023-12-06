from collections import deque
from collections import defaultdict
import heapq

# Read initial inputs
n, m, k = map(int, input().split())

# Init roads
r = defaultdict(lambda: [])
for _ in range(m):
	u, v, w = map(int, input().split())
	r[u - 1].append((v - 1, w))

# Init trips
trips = [] # [t2, u, v, t1, next[]]
for _ in range(k):
	u, v, t1 = map(int, input().split())
	trips.append([0, u - 1, v - 1, t1, []])

# Init list of distances from [u] -> [v]
distances = [[float('inf') for _ in range(n)] for _ in range(n)]
for i in range(n):
	distances[i][i] = 0

# Returns the time required to travel from u to v.
# This problem guarantees that every intersection
# is reachable from every other intersection.
def time(u, v):
	if distances[u][v] != float('inf'):
		return distances[u][v]
	worklist = [u]
	while worklist:
		curr = heapq.heappop(worklist)
		if curr == v:
			return distances[u][curr]
		for neighbor, cost in r[curr]:
			newDist = distances[u][curr] + cost
			if newDist < distances[u][neighbor]:
				distances[u][neighbor] = newDist
				heapq.heappush(worklist, neighbor)

	print(f"Did not find U({u}) -> V({v})")


# Calculate t2 for each trip
for i in range(k):
	t2, u, v, t1, next = trips[i]
	trips[i][0] = t1 + time(u, v)

# Sort by t2 asc
trips.sort()

# Determine next
for i in range(k):
	trip = trips[i]
	myTime = trip[0]
	for j in range(i + 1, k):
		nextTrip = trips[j]
		if nextTrip[3] < myTime:
			continue
		a = time(trip[2], nextTrip[1])
		if  nextTrip[3] < myTime + a:
			continue

		# print(trip, a, nextTrip)
		trip[4].append(j)
		# break # Use to find only the first (nextTrip) for each trip

# Dynamic Programming Algorithm to minimize drivers
# numDrivers[i] = numDrivers[i - 1] + (0 if can reuse driver else 1)
# How will we identify the driver best suited to cover this trip?
# We could choose:
# - The driver who ends closest to us
# Will this always work? I hope so.
drivers = [] # (ending_city_index, available_at_time)[]
for t2, u, v, t1, next in trips:
	moveDistance = [] # (alignmentDriveTime, driverIndex)[]

	# Identify drivers available to serve this trip
	for driverIndex, (driverCity, driverFinishes) in enumerate(drivers):
		if driverFinishes > t1:
			continue
		alignmentDriveTime = time(driverCity, u)
		if driverFinishes + alignmentDriveTime > t1:
			continue
		moveDistance.append((alignmentDriveTime, driverIndex))

	# Pick one
	if moveDistance:
		# Choose the driver who would drive the least to serve us
		moveDistance.sort()
		(_, selectedDriverIndex) = moveDistance[0]
		drivers[selectedDriverIndex] = (v, t2)
	else:
		# We need a new driver
		drivers.append((v, t2))

print(len(drivers))
