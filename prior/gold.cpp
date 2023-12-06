// #include<bits/stdc++.h>
#include<iostream>
#include<vector>

using namespace std;

int r, c;

typedef vector<char> vc;
typedef vector<vc> vvc;

typedef vector<bool> vb;
typedef vector<vb> vvb;

vvc grid;
vvb danger;

int gold = 0;

void solve(int i, int j) {
  if (grid[i][j] == '#') return;
  if (grid[i][j] == 'G') ++gold;

  grid[i][j] = '#';

  solve(i+0, j+1);
  solve(i+0, j-1);
  solve(i+1, j+0);
  solve(i-1, j+0);
}

int main() {
  cin >> c >> r;
  grid.assign(r, vc(c));
  danger.assign(r, vb(c, false));

  for (int i = 0; i<r;++i) for (int j=0;j<c;++j) cin >> grid[i][j];

  // for (int row : grid) {
  //   for (int i : row) cout << i;
  //   cout << endl;
  // }

  int si, sj;
  for (int i = 0; i<r;++i) {
    for (int j=0; j<c;++j) {
      if (grid[i][j] == 'P') {
        si = i;
        sj = j;
      } else if (grid[i][j] == 'T') {
        // Mark all the neighbors as dangerous
      }
    }
  }

  return 0;
}
