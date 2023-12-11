while True:
  v = input()
  if v == "0":
    break
  k, m = map(int, v.split())
  courses = set(input().split())

  valid = True
  for _ in range(m):
    v = input().split()
    if not valid:
      continue

    r = int(v[1])
    for course in v[2:]:
      if course in courses:
        r -= 1
        if r <= 0:
          break

    valid = r <= 0

  print("yes" if valid else "no")
