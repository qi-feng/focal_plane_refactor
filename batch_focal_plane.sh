#!/usr/bin/env bash
set -euo pipefail

ROWS=1944
COLS=2592
INPUT_GLOB="*.raw"
OUTPUT_DIR="batch_outputs"
DO_PSF=0
OVERWRITE=0

# PSF options
SOURCE_ID=""
PSF_X=""
PSF_Y=""
HALFWIDTH=80
ZOOM_HALFWIDTH=20

usage() {
  cat <<EOF
Usage:
  ./batch_focal_plane_psf.sh [options]

Options:
  --input-glob GLOB        Input raw glob (default: *.raw)
  --output-dir DIR         Output directory (default: batch_outputs)
  --rows N                 Raw image rows (default: 1944)
  --cols N                 Raw image cols (default: 2592)
  --do-psf                 Run PSF step
  --overwrite              Overwrite existing outputs

  --source-id ID           Use catalog source ID for PSF
  -p, --point X Y          Use fixed pixel coordinate for PSF
  --halfwidth N            PSF fit halfwidth (default: 80)
  --zoom-halfwidth N       PSF zoom halfwidth (default: 20)

Examples:
  ./batch_focal_plane_psf.sh --do-psf --source-id 25 --overwrite
  ./batch_focal_plane_psf.sh --do-psf -p 1621 1046 --overwrite
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input-glob) INPUT_GLOB="$2"; shift 2 ;;
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --rows) ROWS="$2"; shift 2 ;;
    --cols) COLS="$2"; shift 2 ;;
    --do-psf) DO_PSF=1; shift ;;
    --overwrite) OVERWRITE=1; shift ;;

    --source-id) SOURCE_ID="$2"; shift 2 ;;
    -p|--point) PSF_X="$2"; PSF_Y="$3"; shift 3 ;;
    --halfwidth) HALFWIDTH="$2"; shift 2 ;;
    --zoom-halfwidth) ZOOM_HALFWIDTH="$2"; shift 2 ;;

    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

if [[ $DO_PSF -eq 1 ]]; then
  if [[ -n "$SOURCE_ID" && ( -n "$PSF_X" || -n "$PSF_Y" ) ]]; then
    echo "Use either --source-id or -p/--point, not both."
    exit 1
  fi
  if [[ -z "$SOURCE_ID" && ( -z "$PSF_X" || -z "$PSF_Y" ) ]]; then
    echo "For --do-psf, provide either --source-id ID or -p X Y."
    exit 1
  fi
fi

mkdir -p "$OUTPUT_DIR"

shopt -s nullglob
files=( $INPUT_GLOB )
shopt -u nullglob

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No input files matched: $INPUT_GLOB"
  exit 1
fi

for rawfile in "${files[@]}"; do
  base="$(basename "$rawfile")"
  stem="${base%.raw}"

  catalog="$OUTPUT_DIR/${stem}_catalog.txt"
  preview="$OUTPUT_DIR/${stem}_detections.png"
  preview_raw="$OUTPUT_DIR/${stem}_detections_raw.png"
  dump_jpg="$OUTPUT_DIR/${stem}_stretched.jpg"
  dump_raw_jpg="$OUTPUT_DIR/${stem}_raw.jpg"
  psf_zoom="$OUTPUT_DIR/${stem}_psf_zoom.png"
  psf_overlay="$OUTPUT_DIR/${stem}_psf_overlay.png"

  need_process=1
  if [[ $OVERWRITE -eq 0 && -f "$catalog" && -f "$preview" && -f "$preview_raw" && -f "$dump_jpg" && -f "$dump_raw_jpg" ]]; then
    need_process=0
  fi

  if [[ $need_process -eq 1 ]]; then
    echo "Processing raw: $rawfile"
    python -m focal_plane_refactor.cli process_raw "$rawfile" \
      --rows "$ROWS" --cols "$COLS" \
      --output-catalog "$catalog" \
      --preview "$preview" \
      --preview-raw "$preview_raw" \
      --dump-jpg "$dump_jpg" \
      --dump-raw-jpg "$dump_raw_jpg"
  else
    echo "Skipping process_raw; outputs already exist for $rawfile"
  fi

  if [[ $DO_PSF -eq 1 ]]; then
    need_psf=1
    if [[ $OVERWRITE -eq 0 && -f "$psf_zoom" && -f "$psf_overlay" ]]; then
      need_psf=0
    fi

    if [[ $need_psf -eq 1 ]]; then
      echo "Running PSF for: $rawfile"

      if [[ -n "$SOURCE_ID" ]]; then
        python -m focal_plane_refactor.cli psf "$rawfile" \
          --rows "$ROWS" --cols "$COLS" \
          --catalog "$catalog" \
          --source-id "$SOURCE_ID" \
          --halfwidth "$HALFWIDTH" \
          --zoom-halfwidth "$ZOOM_HALFWIDTH" \
          --use-catalog-shape \
          --annotate-psf \
          --single-contour-2rms \
          --output-zoom "$psf_zoom" \
          --output-overlay "$psf_overlay"
      else
        python -m focal_plane_refactor.cli psf "$rawfile" \
          --rows "$ROWS" --cols "$COLS" \
          --catalog "$catalog" \
          -p "$PSF_X" "$PSF_Y" \
          --halfwidth "$HALFWIDTH" \
          --zoom-halfwidth "$ZOOM_HALFWIDTH" \
          --use-catalog-shape \
          --annotate-psf \
          --single-contour-2rms \
          --output-zoom "$psf_zoom" \
          --output-overlay "$psf_overlay"
      fi
    else
      echo "Skipping psf; outputs already exist for $rawfile"
    fi
  fi
done

echo "Done."
