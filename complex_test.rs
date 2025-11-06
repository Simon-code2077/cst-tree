fn main() {
    println!("Hello, world!");
    let x = 42;
    let y = 100;
    let result = add(x, y);
    println!("Result: {}", result);
}

fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn subtract(x: i32, y: i32) -> i32 {
    x - y
}

fn multiply(a: f64, b: f64) -> f64 {
    a * b
}

fn divide(numerator: f64, denominator: f64) -> f64 {
    numerator / denominator
}

struct Point {
    x: f64,
    y: f64,
}

impl Point {
    fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }
    
    fn distance(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }
}

fn process_numbers() {
    let numbers = vec![1, 2, 3, 4, 5];
    for num in &numbers {
        println!("Number: {}", num);
    }
    
    let sum: i32 = numbers.iter().sum();
    println!("Sum: {}", sum);
}