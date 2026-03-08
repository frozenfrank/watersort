use num::{Num, ToPrimitive};

/// Enum that stores either a forward Range or a reverse Range iterator
pub enum RangeIter<T> {
    Forward(T),
    Reverse(std::iter::Rev<T>),
}

impl<T: DoubleEndedIterator> RangeIter<T> {
    pub fn new(range: T, is_reversed: bool) -> RangeIter<T> {
        match is_reversed {
            false => RangeIter::Forward(range),
            true => RangeIter::Reverse(range.rev()),
        }
    }
}

impl<T: DoubleEndedIterator> Iterator for RangeIter<T> {
    type Item = T::Item;

    fn next(&mut self) -> Option<Self::Item> {
        match self {
            RangeIter::Forward(range) => range.next(),
            RangeIter::Reverse(rev_range) => rev_range.next(),
        }
    }
}

/// Calculates a percentage as a formatted string
pub fn percent_str<T: Num + ToPrimitive, U: Num + ToPrimitive>(value: T, total: U) -> String {
    let value = value.to_f64().unwrap_or(0.0);
    let total = total.to_f64().unwrap_or(0.0);
    if total == 0.0 {
        "0%".to_string()
    } else {
        format!("{:.1}%", (value / total) * 100.0)
    }
}

/// Efficiently replaces an element at one index of a vector with `other`
pub fn vec_replace<T>(vec: &mut Vec<T>, index: usize, other: &mut T) {
    std::mem::swap(&mut vec[index], other);
}

/// Efficiently takes an element at one index of a vector, replacing it with the default value.
pub fn vec_take<T: Default>(vec: &mut Vec<T>, index: usize) -> T {
    let mut existing = T::default();
    vec_replace(vec, index, &mut existing);
    existing
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
