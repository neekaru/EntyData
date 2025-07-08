import re

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


class SimpleVersion:
    def __init__(self, v):
        self.parts = tuple(int(x) for x in v.split('.'))
    def __ge__(self, other):
        return self.parts >= other.parts
    def __le__(self, other):
        return self.parts <= other.parts
    def __eq__(self, other):
        return self.parts == other.parts
    def __lt__(self, other):
        return self.parts < other.parts
    def __gt__(self, other):
        return self.parts > other.parts
    def __repr__(self):
        return f"SimpleVersion({self.parts})"

def version_key(version):
    """Return a tuple for sorting version strings."""
    return v2tuple(version)
