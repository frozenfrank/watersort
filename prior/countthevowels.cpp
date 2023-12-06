// #include<bits/stcd++.h>
#include<iostream>

using namespace std;

int main() {
  char c;

  // getline(cin, s);

  int ans = 0;
  while (cin >> c) {
    c = tolower(c);
    if(c == 'a') ++ans;
    if(c == 'e') ++ans;
    if(c == 'i') ++ans;
    if(c == 'o') ++ans;
    if(c == 'u') ++ans;
  }

  cout << ans;
  cout << endl;
}
