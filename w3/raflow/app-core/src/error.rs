use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("no error")]
    NoError,
}

pub type Result<T> = std::result::Result<T, Error>;
