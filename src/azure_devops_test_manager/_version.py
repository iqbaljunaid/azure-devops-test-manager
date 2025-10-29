import subprocess
import re
from typing import Tuple, Union


def get_git_version() -> Tuple[str, Tuple[Union[int, str], ...], str]:
    try:
        # Get the latest tag description from git
        version_str = (
            subprocess.check_output(
                ["git", "describe", "--tags", "--long"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        # Example format: 1.0.2-dev5-0-g375d8e585 or 1.0.2-5-g375d8e585
        match = re.match(
            r"(\d+\.\d+\.\d+)(?:-(dev)?(\d+))?-(\d+)-g([0-9a-f]+)", version_str
        )
        if match:
            major, minor, patch = map(int, match.group(1).split("."))
            dev_label = f"dev{match.group(3)}" if match.group(3) else None
            commit_id = f"g{match.group(5)}"
            version_parts: list[Union[int, str]] = [major, minor, patch]
            if dev_label:
                version_parts.append(dev_label)
            version_parts.append(commit_id)
            version_tuple = tuple(version_parts)
            version = f"{match.group(1)}"
            if dev_label:
                version += f".{dev_label}"
            version += f"+{commit_id}"
            return version, version_tuple, commit_id
    except Exception:
        pass
    # Fallback default version
    return "0.0.0+unknown", (0, 0, 0, "unknown"), "unknown"


# Get version info from git
__version__, __version_tuple__, __commit_id__ = get_git_version()
version = __version__
version_tuple = __version_tuple__
commit_id = __commit_id__
