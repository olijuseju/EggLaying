# EggLaying — Assisted Egg-Laying Detection in *C. elegans*

> **Human-in-the-loop assistance method for quantifying egg-laying events in *Caenorhabditis elegans* from 4K video recordings.**

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg)]()
[![Paper](https://img.shields.io/badge/Paper-Scientific%20Reports-red.svg)](https://doi.org/YOUR_DOI_HERE)

---

## Associated Publication

> **Development, implementation, and validation of a method for assisting in egg-laying trials in *C. elegans***
> José Julio Peñaranda Jara, Antonio José Sánchez Salmerón
> *Scientific Reports*, 2025
> Affiliated with: Instituto de Automática e Informática Industrial (ai2), Universitat Politècnica de València
> [Read the paper](https://doi.org/YOUR_DOI_HERE)

---

## Overview

Manually annotating egg-laying events in long-duration 4K video recordings of *C. elegans* is time-consuming and prone to missed events. This software implements a **recall-first** human-in-the-loop pipeline that:

1. **Automatically detects** egg-laying candidates using two complementary computer vision approaches
2. **Presents candidates** to the operator via a minimalist GUI for rapid confirmation or rejection
3. **Exports traceable results** as CSV with per-event timestamps and audit trail

### Key results (validated on 6 independent 4K videos, 648,000 frames total)

| Metric | Value |
|--------|-------|
| System-level recall | **0.992** (95% CI: 0.955–0.999) |
| Precision | 0.77 |
| F1-score | 0.85 |
| Review time per 6h video | < 20 min |
| Ground-truth events | 117 across 6 videos |

---

## How It Works

### Automatic Detection Pipeline

Two complementary detectors run in parallel on each video frame, both operating exclusively within a **local worm mask** (M_t) derived from the worm's segmented contour:

**1. Egg-layed detector** (appearance by inter-frame change)
- Computes inter-frame difference images (Δt = It − It−1)
- Filters candidates by area, elliptical shape, skeleton proximity, local contrast, and gradient consistency
- Detects sudden appearance of egg-shaped objects near the worm's vulval region

**2. Tracked-layed detector** (appearance along trajectory)
- Computes sustained-change images against the first frame of each block
- Exploits accumulated worm trajectory to recover slow depositions or occluded events
- Applies temporal persistence filtering to discard transient artefacts

**Fusion logic** merges both detectors by spatio-temporal proximity:
- Dual-branch coincidence → auto-accepted (OK)
- Single-branch, high-confidence → auto-accepted (OK)
- Single-branch, standard confidence → forwarded to human review (NOK)

### Manual Verification Interface

A Tkinter-based GUI presents candidates for rapid binary decisions:
- Synchronized OK/NOK event lists with direct frame navigation
- Overlay layers: worm trajectory, nearest egg marker, morphological detail
- Frame-level adjustment and x2 flag for simultaneous depositions
- Export to CSV with absolute timestamps across 12-minute video blocks

---

## Repository Structure

```
EggLaying/
├── EggLayingLinux/               # Linux version
├── EggLayingWindows/             # Windows version (same codebase, OS-adapted)
├── results/                      # Sample data for one annotated video block
│   ├── 000000.mp4                # Sample video block (12 min, 25 fps)
│   ├── 000001.mp4                # Additional sample block
│   ├── 000000_imgs/              # Diagnostic snippet crops for block 000000
│   ├── 000001_imgs/              # Diagnostic snippet crops for block 000001
│   ├── 000001_rare_poses/        # Flagged rare worm poses for block 000001
│   ├── 000000_metadata_eggs_frames.csv   # Per-event frame numbers (block 000000)
│   ├── 000000_metadata_eggs_times.csv    # Per-event timestamps (block 000000)
│   ├── 000001_metadata_eggs_frames.csv   # Per-event frame numbers (block 000001)
│   ├── 000001_metadata_eggs_times.csv    # Per-event timestamps (block 000001)
│   ├── 000000_ok_eggs_frames.npy         # Auto-accepted candidates (block 000000)
│   ├── 000000_nok_eggs_frames.npy        # Candidates sent to review (block 000000)
│   ├── 000001_ok_eggs_frames.npy         # Auto-accepted candidates (block 000001)
│   ├── 000001_nok_eggs_frames.npy        # Candidates sent to review (block 000001)
│   ├── 000000_poses.npy                  # Worm pose data (block 000000)
│   ├── 000001_poses.npy                  # Worm pose data (block 000001)
│   ├── 000000_track_eggs_frames.npy      # Tracked-layed detections (block 000000)
│   ├── 000001_track_eggs_frames.npy      # Tracked-layed detections (block 000001)
│   └── 000000_img_result_tracking.bmp    # Trajectory visualisation (block 000000)
│   └── 000001_img_result_tracking.bmp    # Trajectory visualisation (block 000001)
└── README.md
```

---

## Sample Data

The `results/` folder contains sample output for two annotated 12-minute video blocks, enabling end-to-end functional testing of the pipeline.

For each block (`000000`, `000001`) the following files are provided:

| File | Description |
|------|-------------|
| `XXXXXX.mp4` | Video block (12 min, 25 fps) |
| `XXXXXX_metadata_eggs_frames.csv` | Validated egg-laying events with frame numbers |
| `XXXXXX_metadata_eggs_times.csv` | Validated egg-laying events with timestamps |
| `XXXXXX_ok_eggs_frames.npy` | Auto-accepted candidates (OK) |
| `XXXXXX_nok_eggs_frames.npy` | Candidates forwarded to manual review (NOK) |
| `XXXXXX_track_eggs_frames.npy` | Tracked-layed detector output |
| `XXXXXX_poses.npy` | Worm skeleton pose data per frame |
| `XXXXXX_img_result_tracking.bmp` | Worm trajectory visualisation over the plate |
| `XXXXXX_imgs/` | 128×128 px diagnostic snippet crops per candidate |
| `XXXXXX_rare_poses/` | Frames flagged as rare worm poses |

---

## Installation

### Linux

```bash
git clone https://github.com/olijuseju/EggLaying.git
cd EggLaying/EggLayingLinux
pip install -r requirements.txt
python main.py
```

### Windows

```bash
git clone https://github.com/olijuseju/EggLaying.git
cd EggLaying/EggLayingWindows
pip install -r requirements.txt
python main.py
```

### Dependencies

```
opencv-python
numpy
pandas
Pillow
scikit-image
tkinter  # included in standard Python on most platforms
```

---

## Detection Parameters

All parameters reproduce exactly the values used in the paper:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Motion threshold | 23 grey levels | Inter-frame difference threshold |
| Dilation kernel | 27×27 ellipse | Local worm mask M_t |
| Egg area range | 18–90 px | Connected component filter |
| Axis ratio | > 0.50 | Elliptical shape criterion |
| Fusion radius | 11.8 px | Spatio-temporal merging distance |
| Skeleton valid range | 56–105 px | Arc length validity |

---

## Experimental Setup

- **Camera:** Motif (Loopbio) 4K system, 3840×2160 px, 5 fps
- **Review speed:** 25 fps (5× real time)
- **Block duration:** 12 minutes (18,000 frames per block)
- **Strain:** *C. elegans* N2 on 55mm NGM plates seeded with *E. coli* OP50
- **Animals:** Young adults, one per plate, freely moving (solid media)

---

## Citation

If you use this software in your research, please cite:

```bibtex
@article{penaranda2025egglaying,
  title={Development, implementation, and validation of a method for
         assisting in egg-laying trials in {C. elegans}},
  author={Peñaranda Jara, José Julio and Sánchez Salmerón, Antonio José},
  journal={Scientific Reports},
  year={2025},
  doi={YOUR_DOI_HERE}
}
```

---

## Acknowledgements

We thank Nuria Flames (Instituto de Biomedicina de Valencia, IBV) for providing the videos and datasets, and Thomas Boulin (Université Claude Bernard Lyon 1) for enabling validation on his equipment.

Funded by Comunitat Valenciana grant INVEST/2023/541 and EU-FEDER Comunitat Valenciana 2014-2020 grant IDIFEDER/2018/025.

---

## Authors

**José Julio Peñaranda Jara** — [GitHub](https://github.com/olijuseju) · [LinkedIn](https://www.linkedin.com/in/jose-julio-pe%C3%B1aranda-jara-b75673206/)
Instituto de Automática e Informática Industrial (ai2), Universitat Politècnica de València

**Antonio José Sánchez Salmerón** — asanchez@isa.upv.es
Instituto de Automática e Informática Industrial (ai2), Universitat Politècnica de València
