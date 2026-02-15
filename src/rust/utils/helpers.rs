use std::ops::Range;

/// Helper functions for the Water Sort Puzzle solver
/// (To be expanded as needed)

/// Enum that stores either a forward Range or a reverse Range iterator
pub enum RangeIter {
    Forward(Range<usize>),
    Reverse(std::iter::Rev<Range<usize>>),
}

impl RangeIter {
    pub fn new(range: Range<usize>, is_reversed: bool) -> RangeIter {
        match is_reversed {
            true => RangeIter::Forward(range),
            false => RangeIter::Reverse(range.rev()),
        }
    }
}

impl Iterator for RangeIter {
    type Item = usize;

    fn next(&mut self) -> Option<usize> {
        match self {
            RangeIter::Forward(range) => range.next(),
            RangeIter::Reverse(rev_range) => rev_range.next(),
        }
    }
}

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
