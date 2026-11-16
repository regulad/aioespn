from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> bytes:
    """A response as ESPN served it, trimmed; see fixtures/README.md."""
    return (FIXTURES / name).read_bytes()
