# Python vs Rust Performance
This watersort solve has now been implemented in two languages: Python and Rust. It was created originally in Python, and core pieces of functionality have been ported to Rust while preserving interoperability and code structure as the original Python implementation.

We will benchmark equivalent output from both programs and compare their performance.

## Test 1: Complete A Game With Commands
In this test, each program will read in moves from the command line. Each move will be valid. The program will apply the move, print out the moves and new game state, and then prompt for the next input. When the game is completed, the program will terminate.

### Python

**Code**
```shell
echo "" > results.txt
for i in {1..100}; do
  echo "Python trial $i"
  (time python src/python/watersort.py 100 < performance_testing/ans-100.txt > /dev/null) 2>> results.txt
  sleep 1
done
```

**Results**

### Rust

**Code**
```shell
cargo build
for i in {1..100}; do
  echo "Rust trial $i"
  (time ./target/debug/watersort 100 < performance_testing/ans-100.txt > /dev/null) 2>> results.txt
  sleep 1
done
```


## Appendix A: Shell Reference

A generic loop for repeating a command 10 times with a delay.
```shell
for i in {1..10}; do
  {command}
  sleep 2
done
```
