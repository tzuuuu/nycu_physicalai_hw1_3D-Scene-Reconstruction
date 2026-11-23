# PhysicalAI26 HW1

This repository contains the HW1 capture simulator and a reconstruction and
experiment workflow. Python dependencies are managed by [Pixi](https://pixi.sh/)
using the checked-in `pixi.lock` file.

## Setup

1. Install Pixi using the instructions at [pixi.sh](https://pixi.sh/).
2. From this directory, create the `habitat` environment:

   ```bash
   pixi install -e habitat
   ```

   The environment provides Python 3.9, Habitat-Sim 0.3.3 with Bullet,
   Habitat-Lab, and the project dependencies. The first install can take a few
   minutes.
3. Check that Habitat-Sim and Habitat-Lab import correctly:

   ```bash
   pixi run -e habitat smoke
   ```

4. Download and extract the Replica apartment scene used by the default
   configuration:

   ```bash
   pixi run -e habitat fetch-replica
   ```

   This creates `replica_v1/apartment_0/`. Keep the scene at that path for the
   default `configs/second_floor.yaml` configuration.

## Capture data

Start the interactive Habitat-Sim collector:

```bash
pixi run -e habitat python load.py
```

The default configuration is `configs/second_floor.yaml`. Captures are written
under `eval/_data/second_floor/` and include RGB and depth PNGs, camera
intrinsics, and a ground-truth pose trajectory. Use `--config` to select a
different configuration or `--output-root` to change the output directory. See
[`docs/load.md`](docs/load.md) for controls, replay mode, and capture details.

## Reconstruction and experiments

Run commands from this repository directory with `pixi run -e habitat`. The
experiment workflow starts by declaring an experiment over a capture, then
reconstructing it:

```bash
pixi run -e habitat python api.py declare \
  --name <experiment-name> \
  --data-dir <capture-directory> \
  --floor 2

pixi run -e habitat python reconstruct.py \
  --experiment experiments/<experiment-name> \
  --no-vis

pixi run -e habitat python api.py explore experiments/<experiment-name>
```

`declare` creates an experiment directory, the first reconstruction measures
pipeline factors and records a baseline, and `explore` displays the results and
writes interactive plots. For the full workflow, SPARQL frame selection, and
query examples, see [`docs/e2e-workflow.md`](docs/e2e-workflow.md).

## Optional Bonus: custom ICP

`utils.my_local_icp_algorithm` implements Point-to-Point ICP with SciPy
`cKDTree` nearest-neighbor queries and a NumPy Kabsch SVD rigid update,
including reflection correction. It does not call Open3D ICP. The original
`local_icp_algorithm` remains unchanged and is still the default backend.

For a **new, unsealed** experiment, explicitly declare the backend by appending
this Turtle statement to its declaration (replace `<name>`):

```turtle
exp:<name> hw1:hasFactorSetting [
    a hw1:FactorSetting ;
    hw1:settingParameter hw1:icpBackend ;
    hw1:settingRole hw1:ReconstructionSetting ;
    hw1:settingForFactor hw1:ReconstructionRun ;
    hw1:settingValue "my_icp"^^xsd:string
] .
```

Then run the existing CLI with `--version my_icp`, preserving the intended
voxel, seed, map voxel, and frame-selection settings. Never edit a sealed
Open3D experiment to switch its backend.

The custom settings are a `1.5 * voxel_size` distance gate, at least 10
correspondences, at most 60 updates, and a `1e-6` metre change in mean inlier
distance for convergence. Collinear support and insufficient correspondences
produce an explicit failure. Final fitness, Euclidean RMSE, and correspondences
are recomputed from the returned transform. GT is used only after reconstruction.

The four-condition study uses Floor 1 baseline (seed 0), Floor 1 C1 (seed 1),
Floor 2 baseline (320 frames), and the frozen Floor 2 sparse-v1 selection
(204 frames). All use registration and map voxels of 0.05 m. Study tooling:

```bash
pixi run -e habitat python scripts/m5_bonus.py prepare
pixi run -e habitat python scripts/m5_bonus.py run
pixi run -e habitat python -m scripts.m5_analysis
pixi run -e habitat python -m scripts.m5_report_assets
```

These commands reserve new fixed output directories and refuse retries or
overwrites. The runner requires native process-table access for its 3 GiB
sampled process-tree RSS guard. Data and historical results must already exist
at the paths recorded in the script. Bonus results go to
`research_outputs/m5_bonus_01/`; three new Bonus experiments contain the four
runs, with the two Floor 2 runs sharing their new custom experiment.

Point-to-Point and the original Point-to-Plane minimize different objectives
and have different stopping rules. Historical runtime boundaries also differ;
recorded times are descriptive and do not establish pure ICP speedup.
The accepted results and limitations are recorded in
[`M5_Bonus_Acceptance.md`](docs/implementation/M5_Bonus_Acceptance.md).
Use `research_outputs/m5_bonus_01/report_assets/` for the reviewed report
figures and English captions; the original analysis drafts are retained.

## More documentation

- [`docs/pixi.md`](docs/pixi.md): environment details and Pixi commands
- [`docs/load.md`](docs/load.md): capture settings, controls, and outputs
- [`docs/reconstruct.md`](docs/reconstruct.md): reconstruction options
- [`docs/api.md`](docs/api.md): experiment and inspection commands
- [`docs/e2e-workflow.md`](docs/e2e-workflow.md): end-to-end walkthrough
