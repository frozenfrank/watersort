#! /bin/zsh

read "test?Test number: "
read "executions?Num executions: "

echo "| Execution | Trials | Python Avg | Rust Debug Avg | % Faster | Rust Avg | % Faster |"
echo "|-----------|--------|------------|----------------|----------|----------|----------|"

total_trials=0

sum_py=0
sum_rd=0
sum_rs=0
sum_pd=0
sum_pr=0

# weighted sums
w_sum_py=0
w_sum_rd=0
w_sum_rs=0

for ((i=1; i<=executions; i++)); do
  py_file="performance_testing/results/test$test/python${i}.txt"
  rd_file="performance_testing/results/test$test/rust-debug${i}.txt"
  rs_file="performance_testing/results/test$test/rust${i}.txt"

  py_avg=$(awk '{s+=$(1);c++} END{if(c) print s/c}' "$py_file")
  rd_avg=$(awk '{s+=$(1);c++} END{if(c) print s/c}' "$rd_file")
  rs_avg=$(awk '{s+=$(1);c++} END{if(c) print s/c}' "$rs_file")

  trials=$(wc -l < "$py_file")

  percent_d=$(awk -v p="$py_avg" -v r="$rd_avg" 'BEGIN{ printf "%.1f", (p/r - 1) * 100 }')
  percent_r=$(awk -v p="$py_avg" -v r="$rs_avg" 'BEGIN{ printf "%.1f", (p/r - 1) * 100 }')

  # accumulate totals
  total_trials=$((total_trials + trials))

  sum_py=$(awk -v a="$sum_py" -v b="$py_avg" 'BEGIN{print a+b}')
  sum_rd=$(awk -v a="$sum_rd" -v b="$rd_avg" 'BEGIN{print a+b}')
  sum_rs=$(awk -v a="$sum_rs" -v b="$rs_avg" 'BEGIN{print a+b}')
  sum_pd=$(awk -v a="$sum_pd" -v b="$percent_d" 'BEGIN{print a+b}')
  sum_pr=$(awk -v a="$sum_pr" -v b="$percent_r" 'BEGIN{print a+b}')

  # weighted sums (avg * trials)
  w_sum_py=$(awk -v a="$w_sum_py" -v b="$py_avg" -v t="$trials" 'BEGIN{print a + (b*t)}')
  w_sum_rd=$(awk -v a="$w_sum_rd" -v b="$rd_avg" -v t="$trials" 'BEGIN{print a + (b*t)}')
  w_sum_rs=$(awk -v a="$w_sum_rs" -v b="$rs_avg" -v t="$trials" 'BEGIN{print a + (b*t)}')

  echo "| $i | $trials | $py_avg | $rd_avg | $percent_d% | $rs_avg | **$percent_r%** |"
done

# simple averages
avg_py=$(awk -v s="$sum_py" -v n="$executions" 'BEGIN{print s/n}')
avg_rd=$(awk -v s="$sum_rd" -v n="$executions" 'BEGIN{print s/n}')
avg_rs=$(awk -v s="$sum_rs" -v n="$executions" 'BEGIN{print s/n}')
avg_pd=$(awk -v s="$sum_pd" -v n="$executions" 'BEGIN{printf "%.1f", s/n}')
avg_pr=$(awk -v s="$sum_pr" -v n="$executions" 'BEGIN{printf "%.1f", s/n}')

# weighted averages
w_avg_py=$(awk -v s="$w_sum_py" -v t="$total_trials" 'BEGIN{print s/t}')
w_avg_rd=$(awk -v s="$w_sum_rd" -v t="$total_trials" 'BEGIN{print s/t}')
w_avg_rs=$(awk -v s="$w_sum_rs" -v t="$total_trials" 'BEGIN{print s/t}')

w_avg_pd=$(awk -v p="$w_avg_py" -v r="$w_avg_rd" 'BEGIN{printf "%.1f", (p/r - 1) * 100 }')
w_avg_pr=$(awk -v p="$w_avg_py" -v r="$w_avg_rs" 'BEGIN{printf "%.1f", (p/r - 1) * 100 }')

# output rows
echo "| **Simple Avg** | $total_trials | $avg_py | $avg_rd | $avg_pd% | $avg_rs | **$avg_pr%** |"
echo "| **Weighted Avg** | $total_trials | $w_avg_py | $w_avg_rd | $w_avg_pd% | $w_avg_rs | **$w_avg_pr%** |"
