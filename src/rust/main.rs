use std::fs;
use std::io;

fn main() {
    println!("Enter the filename:");
    let mut filename = String::new();
    io::stdin().read_line(&mut filename).expect("Failed to read input");
    let filename = filename.trim();

    match fs::read_to_string(filename) {
        Ok(contents) => {
            println!("{}", contents);
        }
        Err(e) => {
            eprintln!("Error reading file: {}", e);
        }
    }
}
