from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SourceDetection:
    x: float
    y: float
    source_id: int | None = None
    a_image: float | None = None
    b_image: float | None = None
    theta_image: float | None = None
    background: float | None = None
    flux_iso: float | None = None


@dataclass
class PSFResult:
    x0: float
    y0: float
    sigma_x: float
    sigma_y: float
    theta: float
    amplitude: float
    background: float
    pix2mm: float | None = None

    @property
    def psf_pix(self) -> float:
        return 2.0 * max(self.sigma_x, self.sigma_y)

    @property
    def psf_mm(self) -> float | None:
        return None if self.pix2mm is None else self.psf_pix * self.pix2mm
