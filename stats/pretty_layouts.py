"""Compatibility wrapper around declarative pretty specs.

All field labels, aliases, parser/formatter metadata and layout declarations
live in stats.pretty_specs. This module is intentionally thin so existing imports
from stats.pretty_layouts keep working during the transition.
"""

from stats.pretty_specs import *  # noqa: F401,F403
