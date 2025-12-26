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
    - [ ] Connected to "blind" mode stored in the game, similar to drain mode
  - [x] Require multiple button presses to advance through multiple spaces
  - [x] Optionally enable/disable the multi-space advance button
  - [x] Add a "Done" screen with checkmarks
  - [x] Add a "Reset" screen at the beginning
  - [ ] Indicate current level in top corner of box
  - [ ] Show number of moves until next color is complete
  - [ ] Show whether path eventually diverges, or extends. Indicate when crossing into new territory.
  - [ ] Indicate whether the steps are discovering a new value or leading to eventual solution
    - [ ] Show summary of color analysis results... surface abnormal colors
  - [ ] Allow leveraging game solver extended menu
- General
  - [x] Automatically store/retrieve monthly game files in annual sub-folders based on current year
  - [ ] Offer to automatically start analysis session of level (in the background)
  - [x] Rename "pour mode" to "drain mode" internally
  - [ ] Introduce intelligent search with heuristics that potentially discover multiple values at once
