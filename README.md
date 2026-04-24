# focal_plane_refactor

Small package for:
- `process_raw`: make a catalog from FITS/raw/image input
- `psf`: fit a Gaussian PSF to one catalog source and save two plots

PSF outputs:
- zoomed raw image around the fitted PSF
- full stretched image with only that PSF contour

Example:

```bash
PYTHONPATH=src python -m focal_plane_refactor.cli psf image.fits \
  --catalog catalog.txt \
  --source-id 301 \
  --halfwidth 80 \
  --zoom-halfwidth 125 \
  --output-zoom psf_zoom.png \
  --output-overlay psf_overlay.png
```


Zoom color scale options:
- `--vmin`
- `--vmax`

Example:

```bash
PYTHONPATH=src python -m focal_plane_refactor.cli psf image.fits \
  --catalog catalog.txt \
  --source-id 301 \
  --halfwidth 80 \
  --zoom-halfwidth 125 \
  --vmin 2500 \
  --vmax 9000 \
  --output-zoom psf_zoom.png \
  --output-overlay psf_overlay.png
```


Use sewpy shape directly for PSF contour:

```bash
PYTHONPATH=src python -m focal_plane_refactor.cli psf image.raw \
  --rows 1944 --cols 2592 \
  --catalog catalog.txt \
  --source-id 46 \
  --halfwidth 10 \
  --zoom-halfwidth 50 \
  --use-catalog-shape \
  --output-zoom psf_zoom.png \
  --output-overlay psf_overlay.png
```


YAML config support
-------------------

You can put most settings in a YAML file and pass it with `--config`.

Example file: `focal_plane_config.example.yml`

Example:
```bash
python -m focal_plane_refactor.cli process_raw image.raw \
  --rows 1944 --cols 2592 \
  --config focal_plane_config.example.yml \
  --output-catalog catalog.txt \
  --preview detections.png \
  --preview-raw detections_raw.png
```

To lower the sewpy threshold, edit:

```yaml
process_raw:
  sewpy:
    config:
      DETECT_MINAREA: 2
      DETECT_THRESH: 2.0
      ANALYSIS_THRESH: 2.0
```
