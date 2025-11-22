mod error;
mod models;

pub use error::{Error, Result};

#[cfg(test)]
mod tests {

    #[test]
    fn test_plus() {
        assert_eq!(1 + 1, 2);
    }
}
