/// Helper functions for the Water Sort Puzzle solver
/// (To be expanded as needed)

/// Calculates a percentage as a formatted string
pub fn percent_str(value: f64, total: f64) -> String {
    if total == 0.0 {
        "0%".to_string()
    } else {
        format!("{:.1}%", (value / total) * 100.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_percent_str() {
        assert_eq!(percent_str(50.0, 100.0), "50.0%");
        assert_eq!(percent_str(0.0, 100.0), "0.0%");
    }
}
