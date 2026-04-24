
from __future__ import annotations
from pathlib import Path
from copy import deepcopy

try:
    import yaml
except Exception:
    yaml = None

DEFAULT_CONFIG = {
    "process_raw": {
        "method": "sewpy",
        "sextractor_path": None,
        "preview": None,
        "preview_raw": None,
        "dump_jpg": None,
        "dump_raw_jpg": None,
        "ellipse_scale": 2.0,
        "simple_detection": {
            "gaussian_sigma": 1.2,
            "percentile_threshold": 99.8,
            "sigma_threshold": 5.0,
            "opening_size": 2,
            "min_pixels": 2,
        },
        "sewpy": {
            "params": [
                "X_IMAGE", "Y_IMAGE", "FLUX_ISO", "FLUX_MAX", "BACKGROUND",
                "A_IMAGE", "B_IMAGE", "THETA_IMAGE", "FLAGS"
            ],
            "config": {
                "DETECT_MINAREA": 3,
                "DETECT_THRESH": 5.0,
                "ANALYSIS_THRESH": 5.0,
                "FILTER": "Y",
                "DEBLEND_NTHRESH": 32,
                "DEBLEND_MINCONT": 0.005,
            },
        },
    },
    "psf": {
        "halfwidth": 50,
        "zoom_halfwidth": 20,
        "annotate_psf": False,
        "single_contour_2rms": False,
        "contour_levels": 6,
        "max_match_radius": 50.0,
        "pix2mm": None,
        "vmin": None,
        "vmax": None,
        "use_catalog_shape": False,
    },
}

def _deep_update(base: dict, updates: dict) -> dict:
    out = deepcopy(base)
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_update(out[k], v)
        else:
            out[k] = v
    return out

def load_config(path: str | Path | None) -> dict:
    cfg = deepcopy(DEFAULT_CONFIG)
    if path is None:
        return cfg
    if yaml is None:
        raise RuntimeError("PyYAML is required for --config support")
    with open(path, "r") as f:
        user_cfg = yaml.safe_load(f) or {}
    return _deep_update(cfg, user_cfg)
