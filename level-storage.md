# Watersort File Definition

An individual watersort level is stored in a file.
It is foreseeable that other file formats may exist it the future.

## `i` Files

The lines in this file are as follows:
1. The letter `i`.
2. The level name without spaces. Then, multiple game mode flags, each separated by a space " " on the same line. Currently accepted flags include:
  - `blind`: the game shows every color with a "?" and rehides it after moving.
  - `mystery`: the game did not reveal all the colors at the beginning.
    - A "blind" game is definitely also a mystery game.
    - A "mystery" game that is not "blind" exposes the top color, but hides the lower colors until they are discovered. Discovering a color reveals all consecutive spaces of the same color.
3. The number of vials `V`.
4. `V` lines where each line holds the value of the space in the vile.
  - `-` indicates an empty space
  - `?` indicates an unknown/mystery value
  - For most levels, there are 1-2 completely empty vials at the end
5. A trailing blank line

### Examples

The file format in abstract terms:
```txt
i
LEVEL_NAME [level_modifiers]
NUM_VIALS
COLOR COLOR COLOR COLOR
COLOR COLOR COLOR COLOR
...

```

A simple demo level:
```txt
i
1
3
r   r   b   b
b   b   r  r
-   -   -   -

```

A level with special modifiers and multiple colors:
```txt
i
jan5 blind mystery
11
p	g	b	m
pk	b	o	pk
pn	pn	pk	o
lb	r	m	b
p	p	lb	m
g	r	lb	o
pk	g	o	m
g	b	p	pn
lb	r	r	pn
-	-	-	-
-	-	-	-

```
