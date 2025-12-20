"""Test version information."""

import slidemaker


def test_version_exists() -> None:
    """Test that version is defined."""
    assert hasattr(slidemaker, "__version__")
    assert isinstance(slidemaker.__version__, str)
    assert len(slidemaker.__version__) > 0


def test_version_format() -> None:
    """Test that version follows semantic versioning."""
    version = slidemaker.__version__
    parts = version.split(".")
    assert len(parts) >= 2  # At least major.minor
    assert parts[0].isdigit()  # Major version is a number
    assert parts[1].isdigit()  # Minor version is a number


def test_author_exists() -> None:
    """Test that author is defined."""
    assert hasattr(slidemaker, "__author__")
    assert isinstance(slidemaker.__author__, str)
    assert len(slidemaker.__author__) > 0


def test_license_exists() -> None:
    """Test that license is defined."""
    assert hasattr(slidemaker, "__license__")
    assert isinstance(slidemaker.__license__, str)
    assert slidemaker.__license__ == "MIT"
