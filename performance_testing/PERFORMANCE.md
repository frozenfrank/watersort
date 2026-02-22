# Python vs Rust Performance
This watersort solve has now been implemented in two languages: Python and Rust. It was created originally in Python, and core pieces of functionality have been ported to Rust while preserving interoperability and code structure as the original Python implementation.

We will benchmark equivalent output from both programs and compare their performance.

**Percent Faster Calculation**

To measure how much faster Rust is compared to Python, we compute the relative speedup by comparing their average execution times. Specifically, we divide the Python runtime by the Rust runtime to determine how many times faster Rust is, then subtract 1 to convert that ratio into a percentage increase in speed.

In mathematical terms, the formula is:

$$\text{Percent Faster} = \left(\frac{T_{\text{Python}}}{T_{\text{Rust}}} - 1\right) \times 100$$

Here, $T_{\text{Python}}$ and $T_{\text{Rust}}$ represent the average execution times of the Python and Rust implementations, respectively. This expresses the performance improvement as a percentage relative to Rust’s runtime.


## Test 1: Complete A Game With Commands
In this test, each program will read in moves from the command line. Each move will be valid. The program will apply the move, print out the moves and new game state, and then prompt for the next input. When the game is completed, the program will terminate.

The results compare the Total time in seconds.


**Average Extraction**
```shell
awk '{ sum += $(NF-1); count++ } END { print sum / count }' results.txt
```

```shell
for file in performance_testing/results/**/*.txt; do
  avg=$(awk '{ sum += $(NF-1); count++ } END { if (count) print sum / count }' "$file")
  echo "$file: $avg"
done
```

```shell
echo "| Execution | Python Avg | Rust Avg | % Faster |"
echo "|---|---------|---------|------------|"
for i in {1..4}; do
  py_file="performance_testing/results/test1/python${i}.txt"
  rs_file="performance_testing/results/test1/rust${i}.txt"

  py_avg=$(awk '{s+=$(NF-1);c++} END{if(c) print s/c}' "$py_file")
  rs_avg=$(awk '{s+=$(NF-1);c++} END{if(c) print s/c}' "$rs_file")

  percent=$(awk -v p="$py_avg" -v r="$rs_avg" 'BEGIN{ printf "%.1f", (p/r - 1) * 100 }')

  echo "| $i | $py_avg | $rs_avg | **$percent%** |"
done
```

### Independent

**Python**
```shell
rm results.txt
for i in {1..100}; do
  echo "Python trial $i"
  (time python src/python/watersort.py 100 < performance_testing/ans-100.txt > /dev/null) 2>> results.txt
  sleep 1
done
mv results.txt performance_testing/results/test1/pythonN.txt
```

**Rust**
```shell
rm results.txt
cargo build
for i in {1..100}; do
  echo "Rust trial $i"
  (time ./target/debug/watersort 100 < performance_testing/ans-100.txt > /dev/null) 2>> results.txt
  sleep 1
done
cp results.txt performance_testing/results/test1/rustN.txt
```

**Results**
| Execution | Python Avg | Rust Avg | % Faster |
|---|---------|---------|--------|
| 1 | 0.08491 | 0.01377 | 516.6% |
| 2 | 0.11936 | 0.02336 | 411.0% |

### Interleaved

**Code**
```zsh
read "execution?Execution Number: "
cargo build
for i in {1..500}; do
  echo "Trial $i"
  (time python src/python/watersort.py 100 < performance_testing/ans-100.txt > /dev/null) 2>> "performance_testing/results/test1/python$execution.txt"
  (time ./target/debug/watersort 100 < performance_testing/ans-100.txt > /dev/null) 2>> "performance_testing/results/test1/rust$execution.txt"
done
```

**Results**

| Execution | Python Avg | Rust Avg | % Faster |
|---|---------|---------|--------|
| 3 | 0.10106 | 0.01506 | 571.0% |
| 4 | 0.096066 | 0.009776 | 882.7% |

### Test 1 - Overall Results

| Execution | Python Avg | Rust Avg | % Faster | Type |
|---|---------|---------|------------|-------------|
| 1 | 0.08491 | 0.01377 | **516.6%** | Independent |
| 2 | 0.11936 | 0.02336 | **411.0%** | Independent |
| 3 | 0.10106 | 0.01506 | **571.0%** | Interleaved |
| 4 | 0.096066 | 0.009776 | **882.7%** | Interleaved |

Therefore, Rust is roughly **4×–9× faster** depending on the run.

## Appendix A: Shell Reference

A generic loop for repeating a command 10 times with a delay.
```shell
for i in {1..10}; do
  {command}
  sleep 2
done
```
