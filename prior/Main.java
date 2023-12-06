import java.util.*;

// https://open.kattis.com/problems/everywhere
public class Main {
  public static void main(String[] args) {
    Scanner in = new Scanner(System.in);

    // The number of test cases
    int n = in.nextInt();

    // Each test case
    for(int i = 0; i < n; i++) {
      var cities = new HashSet<String>();
      int numEntries = in.nextInt();
      in.nextLine();

      for(int j = 0; j < numEntries; j++) {
        String city = in.nextLine();
        cities.add(city);
      }
      System.out.println(cities.size());
    }
  }
}
