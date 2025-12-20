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
