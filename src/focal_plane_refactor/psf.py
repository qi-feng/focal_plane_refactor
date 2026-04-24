from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from .catalog import find_source_by_id, find_source_near, load_catalog
from .image_io import load_image, stretch_to_uint8
from .models import PSFResult


def gaussian2d_rotated(coords, amp, x0, y0, sx, sy, theta, bg):
    x, y = coords
    ct, st = np.cos(theta), np.sin(theta)
    xp = (x - x0) * ct + (y - y0) * st
    yp = -(x - x0) * st + (y - y0) * ct
    return bg + amp * np.exp(-0.5 * ((xp / sx) ** 2 + (yp / sy) ** 2))


def _extract_cutout(image: np.ndarray, x_center: float, y_center: float, halfwidth: int):
    x0 = int(round(x_center))
    y0 = int(round(y_center))
    xmin = max(0, x0 - halfwidth)
    xmax = min(image.shape[1], x0 + halfwidth)
    ymin = max(0, y0 - halfwidth)
    ymax = min(image.shape[0], y0 + halfwidth)
    return image[ymin:ymax, xmin:xmax], xmin, ymin


def fit_psf_in_box(image: np.ndarray, x_center: float, y_center: float, halfwidth: int = 50, pix2mm: float | None = None):
    cutout, xmin, ymin = _extract_cutout(image, x_center, y_center, halfwidth)
    ny, nx = cutout.shape
    y, x = np.mgrid[0:ny, 0:nx]

    bg0 = float(np.median(cutout))
    peak = np.unravel_index(np.argmax(cutout), cutout.shape)
    p0 = [float(cutout.max() - bg0), float(peak[1]), float(peak[0]), 3.0, 3.0, 0.0, bg0]
    bounds = ([0, 0, 0, 0.5, 0.5, -np.pi/2, -np.inf], [np.inf, nx, ny, 40, 40, np.pi/2, np.inf])
    popt, _ = curve_fit(gaussian2d_rotated, (x.ravel(), y.ravel()), cutout.ravel(), p0=p0, bounds=bounds, maxfev=40000)
    fit_image = gaussian2d_rotated((x, y), *popt).reshape(cutout.shape)
    result = PSFResult(
        x0=float(popt[1]), y0=float(popt[2]), sigma_x=float(popt[3]), sigma_y=float(popt[4]),
        theta=float(popt[5]), amplitude=float(popt[0]), background=float(popt[6]), pix2mm=pix2mm,
    )
    return result, cutout, fit_image, xmin, ymin


def fit_psf_from_catalog(
    image_path: str,
    catalog_path: str,
    x_guess: float | None = None,
    y_guess: float | None = None,
    source_id: int | None = None,
    halfwidth: int = 50,
    shape: tuple[int, int] | None = None,
    pix2mm: float | None = None,
    fits_hdu: int = 0,
    max_match_radius: float = 50.0,
    use_catalog_shape: bool = False,
):
    image = load_image(image_path, shape=shape, fits_hdu=fits_hdu)
    catalog = load_catalog(catalog_path)
    if source_id is not None:
        src = find_source_by_id(catalog, source_id)
    else:
        if x_guess is None or y_guess is None:
            raise ValueError('Either source_id or x_guess/y_guess must be provided')
        src = find_source_near(catalog, x_guess, y_guess, max_radius=max_match_radius)

    if use_catalog_shape:
        cutout, xmin, ymin = _extract_cutout(image, src.x, src.y, halfwidth)
        ny, nx = cutout.shape
        y, x = np.mgrid[0:ny, 0:nx]
        bg = float(np.median(cutout))
        amp = float(max(cutout.max() - bg, 1.0))
        x0 = float(src.x - xmin)
        y0 = float(src.y - ymin)
        sx = float(src.a_image if src.a_image is not None else 3.0)
        sy = float(src.b_image if src.b_image is not None else 3.0)
        theta = float(np.deg2rad(src.theta_image if src.theta_image is not None else 0.0))
        fit_image = gaussian2d_rotated((x, y), amp, x0, y0, sx, sy, theta, bg).reshape(cutout.shape)
        result = PSFResult(
            x0=x0, y0=y0, sigma_x=sx, sigma_y=sy, theta=theta,
            amplitude=amp, background=bg, pix2mm=pix2mm,
        )
    else:
        result, cutout, fit_image, xmin, ymin = fit_psf_in_box(image, src.x, src.y, halfwidth=halfwidth, pix2mm=pix2mm)

    return result, cutout, fit_image, xmin, ymin, src


def _psf_levels(result: PSFResult, single_contour_2rms: bool, contour_levels: int):
    if single_contour_2rms:
        return [result.background + result.amplitude * np.exp(-2.0)]
    frac = np.linspace(0.2, 0.9, contour_levels)
    return result.background + result.amplitude * frac


def plot_psf_zoom(image: np.ndarray, result: PSFResult, fit_image: np.ndarray, xmin: int, ymin: int, zoom_halfwidth: int = 20, annotate_psf: bool = False, single_contour_2rms: bool = False, contour_levels: int = 6, vmin: float | None = None, vmax: float | None = None):
    xg = xmin + result.x0
    yg = ymin + result.y0
    x1 = max(0, int(round(xg - zoom_halfwidth)))
    x2 = min(image.shape[1], int(round(xg + zoom_halfwidth)))
    y1 = max(0, int(round(yg - zoom_halfwidth)))
    y2 = min(image.shape[0], int(round(yg + zoom_halfwidth)))

    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(image[y1:y2, x1:x2], origin='lower', vmin=vmin, vmax=vmax)

    yy, xx = np.mgrid[ymin:ymin + fit_image.shape[0], xmin:xmin + fit_image.shape[1]]
    ax.contour(xx - x1, yy - y1, fit_image, levels=_psf_levels(result, single_contour_2rms, contour_levels), colors='white', linewidths=1.5)
    ax.plot(xg - x1, yg - y1, '+', color='red', markersize=14, markeredgewidth=2)
    ax.set_title('PSF zoom')
    ax.set_xlabel('x [pix]')
    ax.set_ylabel('y [pix]')
    if annotate_psf:
        text = f'2σx = {2*result.sigma_x:.2f} pix\n2σy = {2*result.sigma_y:.2f} pix\nPSF = {result.psf_pix:.2f} pix'
        if result.psf_mm is not None:
            text += f'\nPSF = {result.psf_mm:.3f} mm'
        ax.text(0.03, 0.97, text, transform=ax.transAxes, va='top', ha='left', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    fig.colorbar(im, ax=ax, label='counts')
    return fig


def plot_psf_overlay(image: np.ndarray, result: PSFResult, fit_image: np.ndarray, xmin: int, ymin: int, single_contour_2rms: bool = False, contour_levels: int = 6):
    stretched = stretch_to_uint8(image)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(stretched, origin='lower', cmap='gray', vmin=0, vmax=255)
    yy, xx = np.mgrid[ymin:ymin + fit_image.shape[0], xmin:xmin + fit_image.shape[1]]
    ax.contour(xx, yy, fit_image, levels=_psf_levels(result, single_contour_2rms, contour_levels), colors='red', linewidths=1.2)
    ax.plot(xmin + result.x0, ymin + result.y0, '+', color='yellow', markersize=10, markeredgewidth=1.5)
    ax.set_title('Full image with PSF contour')
    ax.set_xlabel('x [pix]')
    ax.set_ylabel('y [pix]')
    return fig
