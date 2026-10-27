"""Short lane resources and explicit cache adapters, independent of workspace depth."""
import hashlib
import os
from pathlib import Path
import tempfile


def resource_root(identity):
    """Use the account's local temp on Windows even when TMP points into a deep checkout."""
    base = Path(os.environ["LOCALAPPDATA"]) / "Temp" if os.name == "nt" else Path(tempfile.gettempdir())
    root = base / "factory-lanes" / hashlib.sha256(str(identity).encode()).hexdigest()[:20]
    if os.name == "nt" and len(str(root)) > 160:
        raise ValueError("Account temp path is too long for a short browser profile")
    root.mkdir(parents=True, exist_ok=True)
    return root


def environment(root):
    """Wire supported tools; other build systems must explicitly use FACTORY_CACHE_DIR."""
    root = Path(root)
    paths = {"FACTORY_CACHE_DIR": "cache", "CARGO_TARGET_DIR": "cache/cargo",
             "CARGO_BUILD_BUILD_DIR": "cache/cargo-build", "npm_config_cache": "cache/npm",
             "PYTHONPYCACHEPREFIX": "cache/python", "FACTORY_PROFILE_DIR": "profiles"}
    result = dict(os.environ)
    for name, relative in paths.items():
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        result[name] = str(path)
    return result


def profile(identity):
    """A unique profile below the short lane root, suitable for any browser harness."""
    root = resource_root(identity) / "profiles"
    root.mkdir(exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="p-", dir=root))
