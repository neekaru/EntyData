import re

class VersionHandling:
    """Utilities for handling version strings."""

    @staticmethod
    def v2tuple(v):
        """Convert a version string to a tuple of integers for comparison."""
        parts = re.split(r'\.|-', v)
        nums = []
        for part in parts:
            if part.isdigit():
                nums.append(int(part))
            else:
                break
        return tuple(nums)

    @staticmethod
    def version_key(version):
        """Return a tuple for sorting version strings."""
        return VersionHandling.v2tuple(version)


class SimpleVersion:
    def __init__(self, v):
        """
        Initialize a SimpleVersion object.

        Args:
            v: A version string (e.g. "1.2.3")
        """
        self.parts = tuple(int(x) for x in v.split('.'))
    def __ge__(self, other):
        """Compare two versions for greater than or equal to.

        Args:
            other: A SimpleVersion object

        Returns:
            True if self is greater than or equal to other, False otherwise.
        """
        return self.parts >= other.parts
    def __le__(self, other):
        """Compare two versions for less than or equal to.

        Args:
            other: A SimpleVersion object

        Returns:
            True if self is less than or equal to other, False otherwise.
        """

        return self.parts <= other.parts
    def __eq__(self, other):
        """Compare two versions for equality.

        Args:
            other: A SimpleVersion object

        Returns:
            True if self is equal to other, False otherwise.
        """
        return self.parts == other.parts
    def __lt__(self, other):
        """Compare two versions for less than.

        Args:
            other: A SimpleVersion object

        Returns:
            True if self is less than other, False otherwise.
        """
        return self.parts < other.parts
    def __gt__(self, other):
        """Compare two versions for greater than.

        Args:
            other: A SimpleVersion object

        Returns:
            True if self is greater than other, False otherwise.
        """

        return self.parts > other.parts
    def __repr__(self):
        """Return a string representation of the version.

        Returns:
            A string of the form "SimpleVersion(X.Y.Z)"
        """
        return f"SimpleVersion({self.parts})"

