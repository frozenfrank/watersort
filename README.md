# Watersort Readme

## Moving Daily tests into annual folders

```shell
# Replace YEAR_NUM and FILE_GLOB with appropriate values for your use case
cd wslevels
mkdir YEAR_NUM
git log FILE_GLOB
for file in FILE_GLOB; do git mv $file "YEAR_NUM/$file";  done
git mv level.txt YEAR/level.txt
```

## Ideas/Todo

- Big Solution Display
  - [x] Display big progress dots for multiple colors to move
    - [x] Connected to "blind" mode stored in the game, similar to drain mode
  - [x] Require multiple button presses to advance through multiple spaces
  - [x] Optionally enable/disable the multi-space advance button
  - [x] Add a "Done" screen with checkmarks
  - [x] Add a "Reset" screen at the beginning
  - [x] Indicate current level in top corner of box
  - [ ] Show number of moves until next color is complete
  - [ ] Show whether path eventually diverges, or extends. Indicate when crossing into new territory.
  - [ ] Indicate whether the steps are discovering a new value or leading to eventual solution
    - This could be implemented with a context-provided message by the code launching the solution stepper
    - [ ] Show summary of color analysis results... surface abnormal colors
  - [x] Allow leveraging game solver extended menu
    - [ ] Add ability to manually play a game from any step
    - [ ] Add option to launch solver from any step
    - [x] Implement help menu
  - [ ] Reuse terminal space instead of bumping things out of the terminal history
- Solver Refactor
  - [x] Fix BFS continuation after discovering all unknowns. Currently "switches" to DFS 200 times before reporting "reset"
- General
  - [x] Automatically store/retrieve monthly game files in annual sub-folders based on current year
  - [ ] Offer to automatically start analysis session of level (in the background)
  - [x] Rename "pour mode" to "drain mode" internally
  - [ ] Introduce intelligent search with heuristics that potentially discover multiple values at once
  - [ ] Analyze at what point the game is "safe" (no more dead ends)
    - [ ] Show the safe point on the big solution solver
    - [ ] Install an early exit after discovering 999 dead ends
    - [ ] Show the number of dead ends from each step forward
    - [ ] Create mechanisms for viewing the paths to dead ends
  - [ ] Analyze which colors are used most frequently in levels (yellow is uncommon)
  - [ ] Add support for leveraging the "UNDO" feature to look for new vials after discovering colors
    - Only use UNDO if it would otherwise restart
    - Include the configurable UNDO limit of 5 per game
  - [ ] Forward unsupported game commands back a level to apply in the upper game level
