num = int(input())

while num:
  num -= 1

  alphabet = set(list("abcdefghijklmnopqrstuvwxyz"))
  line = input().lower()
  for char in line:
    if char in alphabet:
      alphabet.remove(char)

  if len(alphabet) == 0:
    print("pangram")
  else:
    missingChars = "".join(sorted(alphabet))
    print("missing %s" % missingChars)
