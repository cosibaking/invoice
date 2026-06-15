"""
Load runtime settings from YAML with optional local override.
"""
import copy
import os

try:
    import yaml
except ImportError:
    yaml = None

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_SETTINGS = os.path.join(_PROJECT_ROOT, 'config', 'settings.yaml')
_SETTINGS = None


def _deep_merge(base, override):
    """Recursively merge override into base (override wins)."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _load_yaml(path):
    if yaml is None:
        raise ImportError('PyYAML is required. Install with: pip install PyYAML')
    if not os.path.isfile(path):
        return {}
    with open(path, 'r', encoding='utf-8') as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def _settings_paths():
    base_path = os.environ.get('SETTINGS_PATH', '').strip() or _DEFAULT_SETTINGS
    base_path = os.path.abspath(base_path)
    local_path = os.path.join(os.path.dirname(base_path), 'settings.local.yaml')
    return base_path, local_path


def load_settings():
    """Load settings.yaml and merge settings.local.yaml if present."""
    base_path, local_path = _settings_paths()
    settings = _load_yaml(base_path)
    if os.path.isfile(local_path):
        settings = _deep_merge(settings, _load_yaml(local_path))
    return settings


def get_settings():
    """Return cached settings dict (reload on first call only)."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = load_settings()
    return _SETTINGS


def reset_settings_cache():
    """Clear cached settings (for tests)."""
    global _SETTINGS
    _SETTINGS = None
