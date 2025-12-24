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
  - [ ] Display big progress dots for multiple colors to move
    - [ ] Connected to "blind" mode stored in the game, similar to pour mode
  - [ ] Require multiple button presses to advance through multiple spaces
  - [ ] Optionally enable/disable the multi-space advance button
  - [ ] Add a "Done" screen with checkmarks
  - [ ] Indicate current level in top corner of box
  - [ ] Show number of moves until next color is complete
  - [ ] Show whether path eventually diverges, or extends. Indicate when crossing into new territory.
  - [ ] Indicate whether the steps are discovering a new value or leading to eventual solution
    - [ ] Show summary of color analysis results... surface abnormal colors
  - [ ] Allow leveraging game solver extended menu
- General
  - [ ] Automatically store/retrieve monthly game files in annual sub-folders based on current year
  - [ ] Offer to automatically start analysis session of level (in the background)
  - [ ] Rename "pour mode" to "drain mode" internally
