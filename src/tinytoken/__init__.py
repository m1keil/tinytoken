from pkg_resources import get_distribution, DistributionNotFound
from pathlib import Path

BASE = Path('~/.tinytoken')

try:
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound
