# EggLaying — Assisted egg-laying quantification in *C. elegans* 4K video

This repository contains the implementation of the human-in-the-loop method described in:

> Peñaranda Jara, J.J. & Sánchez Salmerón, A.J. (2025). *Development, implementation, and validation of a method for assisting in egg-laying trials in C. elegans.* Computers in Biology and Medicine.

The method combines two complementary automatic detectors with a manual verification GUI to achieve near-complete egg-laying event recovery (recall 0.992) from long-duration 4K video recordings, with operator review times of 10–15 minutes per 6-hour video.

---

## Repository structure

```
EggLaying/
├── EggLayingLinux/          # Linux version
│   ├── gui.py               # Main entry point: launches the full interface
│   ├── lib.py               # Detection pipeline (egg-layed + tracked-layed + fusion)
│   ├── config.yaml          # All pipeline parameters (edit to adapt the method)
│   ├── prev_icon.png        # Playback control icons (required at runtime)
│   ├── pause_icon.png
│   ├── next_icon.png
│   ├── backward_icon.png
│   └── forward_icon.png
├── EggLayingWindows/        # Windows version (identical logic)
│   └── (same files as above)
├── sample_data/             # Sample annotated block for end-to-end testing
│   ├── sample_block.mp4     # One 12-minute block compressed at 25 fps
│   └── sample_gt.csv        # Ground-truth annotations for the sample block
└── requirements.txt         # Pinned Python dependencies
```

---

## Requirements

- Python 3.8 or later
- See `requirements.txt` for all pinned dependencies

Install dependencies:

```bash
pip install -r requirements.txt
```

### Linux

No additional system dependencies beyond Python and `requirements.txt`.

### Windows

Tkinter is included with standard Python distributions on Windows. If missing, reinstall Python from [python.org](https://www.python.org) and ensure the "tcl/tk and IDLE" option is selected during installation.

---

## Installation

### Linux

```bash
git clone https://github.com/olijuseju/EggLaying.git
cd EggLaying/EggLayingLinux
pip install -r ../requirements.txt
```

### Windows

```bash
git clone https://github.com/olijuseju/EggLaying.git
cd EggLaying\EggLayingWindows
pip install -r ..\requirements.txt
```

---

## Folder structure expected at runtime

The application expects video data organised as follows:

```
egg_laying/                          <- working_path (selected via GUI or restored from rutas.txt)
└── <assay_name>/                    <- one subfolder per assay
    ├── 0.mp4                        <- 12-minute review blocks at 25 fps, named 0, 1, 2...
    ├── 1.mp4
    └── ...

egg_laying_new/                      <- created automatically at the same level as egg_laying/
└── <assay_name>/
    ├── 0_ok_eggs_frames.npy         <- auto-accepted events (saved after every action)
    ├── 0_nok_eggs_frames.npy        <- uncertain events sent to human review
    ├── 0_track_eggs_frames.npy      <- tracked-layed detections
    ├── 0_metadata_eggs_frames.csv   <- per-event spatial metadata (frame, centroid x/y)
    ├── 0_img_result_tracking.bmp    <- full worm trajectory overlay image
    ├── 0_imgs/                      <- 128x128 px diagnostic snippets per candidate
    └── metadata_eggs_final.csv      <- consolidated export with absolute timestamps
```

The last used `working_path` is saved automatically to `rutas.txt` in the application directory and restored on next launch.

---

## Usage

### Step 1 — Launch the application

```bash
# Linux
cd EggLayingLinux
python gui.py

# Windows
cd EggLayingWindows
python gui.py
```

On first launch, select the working folder (`egg_laying/`) using the **Change working folder** button in the **Processing** tab. The output folder `egg_laying_new/` is created automatically next to it.

### Step 2 — Run the automatic detection pipeline (Processing tab)

1. Select an assay from the left list.
2. Click a video in the right list to process a single 12-minute block.
3. Or click **Process all videos** to process all blocks of the selected assay sequentially.
4. Or click **Process all assays** to process all assays in the working folder (parallel threads).

Completed videos are highlighted in blue in the list.

### Step 3 — Review candidates (Checking tab)

Switch to the **Checking** tab (or press `c`):

1. Select a video from the right-hand list.
2. The interface populates two synchronised lists:
   - **NOK list** (left, red): uncertain candidates requiring a decision.
   - **OK list** (right, green): automatically accepted events.

Use the five-action decision set:

| Action | Description |
|--------|-------------|
| **Move to OK** | Confirm a NOK candidate as a genuine egg-laying event |
| **Move to NOK** | Reclassify an auto-accepted event as spurious |
| **Delete** | Remove a candidate permanently from either list |
| **Undo** | Revert the last action on either list |
| **x2** | Duplicate an event (two eggs deposited simultaneously, registered as one detection) |

All decisions are saved incrementally to `.npy` files after each action, preventing data loss on interruption.

Navigation shortcuts:

| Key | Action |
|-----|--------|
| `p` | Switch to Processing tab |
| `c` | Switch to Checking tab, focus video list |
| `o` | Focus OK list, jump to first item |
| `n` | Focus NOK list, jump to first item |
| `←` `→` | Step one frame backward / forward |
| `↑` `↓` | Move to previous / next event in the active list |
| `+` / `-` | Increase / decrease the frame-skip increment |

Overlay toggles (bottom-right panel):

| Toggle | Description |
|--------|-------------|
| **Mark nearest egg** | Draws a circle at the nearest confirmed egg position on the video |
| **Show track** | Opens a floating window with the full worm trajectory overlay |
| **Show worm details** | Opens a floating window with a crop from the original 4K frame |

Fine temporal adjustment: type the corrected frame number in the entry field below the diagnostic snippet and press Enter (or click **Edit & Order**).

### Step 4 — Export results

**Save results of this video** (Checking tab): writes two CSV files per block into `egg_laying_new/<assay>/`:
- `<video>_metadata_eggs_times_final.csv` — timestamps (hh:mm:ss) relative to block start.
- `<video>_metadata_eggs_frames_final.csv` — frame numbers within the block at 25 fps.

**Save results of this assay** (Processing tab): consolidates all per-block CSVs into a single `metadata_eggs_final.csv` with absolute timestamps:

```
t_abs (seconds) = frame_number / 25 + block_index * 720
```

where 720 = 12 minutes × 60 seconds per block. The output columns are:
`full_data` (hh:mm:ss), `video` (block index), `frame_num`.

---

## End-to-end functional test with sample data

1. Place `sample_data/sample_block.mp4` in `egg_laying/sample/0.mp4`.
2. Launch `gui.py` and select the `egg_laying/` parent as the working folder.
3. Select the `sample` assay, click the block in the right list to process it.
4. Switch to the Checking tab, select the processed block, and review candidates.
5. Click **Save results of this video** and compare the exported `frame_num` column against `sample_data/sample_gt.csv`.

---

## Citation

If you use this code or method, please cite:

```bibtex
@article{Penaranda2025_EggLayingCode,
  author    = {Pe{\~n}aranda Jara, Jos{\'e} Julio and
               S{\'a}nchez Salmer{\'o}n, Antonio Jos{\'e}},
  title     = {Development, implementation, and validation of a method
               for assisting in egg-laying trials in \textit{C. elegans}},
  journal   = {Computers in Biology and Medicine},
  year      = {2025},
  note      = {Code: \url{https://github.com/olijuseju/EggLaying}}
}
```

---

## Acknowledgements

We thank Nuria Flames (Instituto de Biomedicina de Valencia, IBV) for providing the experimental videos and datasets, and Thomas Boulin (Université Claude Bernard Lyon 1) for testing the code on independent equipment.

This work was supported by Comunitat Valenciana (Spain) under grant INVEST/2023/541 and EU-FEDER grant IDIFEDER/2018/025.
