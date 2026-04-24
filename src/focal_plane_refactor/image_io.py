from __future__ import annotations
from pathlib import Path

import numpy as np
from astropy.io import fits
from PIL import Image


IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}


def load_image(path: str | Path, shape: tuple[int, int] | None = None, fits_hdu: int = 0, dtype=np.uint8) -> np.ndarray:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in {'.fits', '.fit', '.fts'}:
        with fits.open(path) as hdul:
            data = np.asarray(hdul[fits_hdu].data)
        data = np.squeeze(data)
        if data.ndim != 2:
            raise ValueError(f'Expected 2D FITS image, got shape {data.shape}')
        return data.astype(float)

    if suffix == '.raw':
        if shape is None:
            raise ValueError('shape must be provided for raw files')
        arr = np.fromfile(path, dtype=dtype)
        expected = int(np.prod(shape))
        if arr.size != expected:
            raise ValueError(f'Raw file size mismatch: got {arr.size}, expected {expected}')
        return arr.reshape(shape).astype(float)

    if suffix in IMAGE_SUFFIXES:
        arr = np.asarray(Image.open(path).convert('L'))
        return arr.astype(float)

    raise ValueError(f'Unsupported image format: {path}')


def stretch_to_uint8(image: np.ndarray, lo: float = 1.0, hi: float = 99.0) -> np.ndarray:
    data = np.nan_to_num(np.asarray(image, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    vmin, vmax = np.percentile(data, [lo, hi])
    if vmax <= vmin:
        return np.zeros(data.shape, dtype=np.uint8)
    scaled = np.clip((data - vmin) / (vmax - vmin), 0.0, 1.0)
    return (255.0 * scaled).astype(np.uint8)


def linear_to_uint8(image: np.ndarray) -> np.ndarray:
    data = np.nan_to_num(np.asarray(image, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    vmin, vmax = data.min(), data.max()
    if vmax <= vmin:
        return np.zeros(data.shape, dtype=np.uint8)
    return (255.0 * (data - vmin) / (vmax - vmin)).astype(np.uint8)
