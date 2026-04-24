from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io import fits

from focal_plane_refactor.catalog import find_source_by_id
from focal_plane_refactor.detect import process_raw
from focal_plane_refactor.psf import fit_psf_from_catalog, plot_psf_overlay, plot_psf_zoom


def test_process_raw_and_source_id(tmp_path: Path):
    y, x = np.mgrid[0:100, 0:120]
    img = 100 + 500 * np.exp(-0.5 * (((x-60)/2.5)**2 + ((y-40)/3.0)**2))
    fits_path = tmp_path / 'test.fits'
    fits.writeto(fits_path, img, overwrite=True)
    cat_path = tmp_path / 'cat.txt'
    df = process_raw(fits_path, cat_path, method='simple_detection')
    assert cat_path.exists()
    assert len(df) >= 1
    src = find_source_by_id(pd.read_csv(cat_path, sep=r'\s+', engine='python'), 0)
    assert src.source_id == 0


def test_psf_plots(tmp_path: Path):
    y, x = np.mgrid[0:80, 0:80]
    img = 10 + 200 * np.exp(-0.5 * (((x-35)/2.0)**2 + ((y-45)/3.0)**2))
    fits_path = tmp_path / 'test.fits'
    fits.writeto(fits_path, img, overwrite=True)
    cat_path = tmp_path / 'cat.txt'
    pd.DataFrame([{'ID': 301, 'X_IMAGE': 35.0, 'Y_IMAGE': 45.0}]).to_csv(cat_path, sep=' ', index=False)
    result, cutout, fit_image, xmin, ymin, src = fit_psf_from_catalog(str(fits_path), str(cat_path), source_id=301, halfwidth=20)
    assert src.source_id == 301
    fig1 = plot_psf_zoom(img, result, fit_image, xmin, ymin, zoom_halfwidth=25)
    fig2 = plot_psf_overlay(img, result, fit_image, xmin, ymin)
    assert fig1 is not None and fig2 is not None
