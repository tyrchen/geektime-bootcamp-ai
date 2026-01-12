"""Blake3 hash computation utilities."""

import blake3


def compute_blake3(content: str) -> str:
    """
    Compute the blake3 hash of a string (first 16 characters).

    Args:
        content: The string content to hash

    Returns:
        The first 16 characters of the blake3 hash in hexadecimal format
    """
    return blake3.blake3(content.encode("utf-8")).hexdigest()[:16]
