"""Curate existing Bonus figures and repair 3D labels; no registration or fusion."""
import os
from pathlib import Path
import shutil

os.environ.setdefault('MPLCONFIGDIR', '/tmp/m5-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
from scripts.m5_bonus import ROOT, OUT, CONDITIONS, expected_frames, read
from scripts.m5_analysis import sampled_map, gt_camera
from scripts.m42_monitor import write
from scripts.m4_capture_check import sha


def render():
    destination = OUT/'report_assets'
    destination.mkdir(exist_ok=False)
    figures = destination/'figures'
    figures.mkdir()
    manifest = {}
    captions = []
    for original in sorted((OUT/'analysis/figures').glob('*.png')):
        if original.name.endswith('_custom_3d.png'):
            continue
        target = figures/original.name
        shutil.copyfile(original, target)
        manifest[original.name] = dict(action='byte-for-byte copy', source=str(original.relative_to(ROOT)),
                                       source_sha256=sha(original), sha256=sha(target))
    for key, spec in CONDITIONS.items():
        obs = OUT/key/'observation'
        points, colors = sampled_map(obs)
        prediction = np.load(obs/'positions.npy')
        truth = gt_camera(ROOT/spec['capture'], expected_frames(key))
        fig = plt.figure(figsize=(11, 8))
        ax = fig.add_axes([.02, .08, .79, .83], projection='3d')
        ax.scatter(points[:, 0], points[:, 2], -points[:, 1], c=colors,
                   s=.35, linewidths=0, rasterized=True)
        for path, color, label in [(prediction, 'red', 'Estimated'), (truth, 'black', 'Ground truth')]:
            ax.plot(path[:, 0], path[:, 2], -path[:, 1], c=color, label=label, lw=1.4)
        span = np.ptp(np.concatenate([points, prediction, truth]), axis=0)
        ax.set_box_aspect(np.maximum(span[[0, 2, 1]], .01))
        ax.set(xlabel='Camera X (m)', ylabel='Camera Z (m)', zlabel='')
        ax.zaxis.set_major_locator(MaxNLocator(4))
        ax.tick_params(labelsize=9)
        ax.view_init(35, -55)
        ax.legend(loc='upper left', fontsize=10)
        # Figure text is included by bbox_inches; Matplotlib's 3D axis label
        # can lie outside its own bounding box at the physical aspect ratio.
        fig.text(.91, .50, 'Height (-Y, m)', rotation=90, va='center', ha='center', fontsize=11)
        mean = read(obs/'official_evaluation.json')['mean_l2_raw_m']
        fig.suptitle('%s | Custom Point-to-Point ICP | N=%d | Mean L2 %.6f m'%
                     (key, spec['n'], mean), fontsize=13, y=.97)
        name = key+'_custom_3d.png'
        target = figures/name
        fig.savefig(target, dpi=200, bbox_inches='tight', pad_inches=.2)
        plt.close(fig)
        sources = {str((obs/(n+'.npy')).relative_to(ROOT)):sha(obs/(n+'.npy'))
                   for n in ['map_points','map_colors','positions']}
        manifest[name] = dict(action='render saved map; label-only display revision',
            sources=sources, sha256=sha(target), display_points=len(points),
            axes='camera X, camera Z, negative camera Y (height)', view_elevation=35, view_azimuth=-55,
            original_draft=str((OUT/'analysis/figures'/name).relative_to(ROOT)))
    common = ('Maps use the first captured camera reference without fitted alignment. Estimated trajectories '
              'are red and ground truth is black. The teacher ceiling-removal rule was applied during reconstruction. '
              'Display samples contain at most 90,000 deterministically spaced saved points; complete custom maps '
              'remain separately stored. Blank regions do not establish missing-room or absolute surface completeness.')
    for name in sorted(manifest):
        if name.endswith('_native.png'):
            text = ('Original historical and custom native screenshots. Their viewpoints and limits may differ; '
                    'use the paired map figure for common-axis comparison.')
        elif name == 'f1_baseline_maps.png':
            text = ('Floor 1 baseline: the historical panel shows the previously verified matching M3.0 diagnostic '
                    'trajectory because the original M2 full map was not saved. The custom panel shows this run. '
                    'Both panels share camera X/Z limits and scale. '+common)
        elif name == 'f1_c1_maps.png':
            text = ('Floor 1 C1: historical saved stride sample versus the new custom map sample, with common axes. '+common)
        elif name.endswith('_maps.png') or name.startswith('custom_f'):
            text = 'Paired maps use common limits and equal scale. '+common
        elif name == 'custom_overview.png':
            text = 'Four custom reconstructions; each overview panel has its own limits. '+common
        elif name.endswith('_custom_3d.png'):
            text = '3D view of the same-run saved custom map, with repaired label placement and physical aspect ratio. '+common
        elif name.endswith('_factors.png'):
            text = ('Eight raw factors from historical and custom runs. Input and RANSAC factors overlap when '
                    'identical; selected custom factors are new same-run observer measurements, not sealed baseline factors. '
                    'RMSE is Euclidean correspondence RMSE, not the Point-to-Plane objective or trajectory error.')
        elif name == 'custom_iterations.png':
            text = 'Custom ICP update counts; the dashed line is the 60-update budget. Reaching it is not convergence.'
        elif name == 'per_frame_l2.png':
            text = 'Per-frame camera-center errors against evaluation-only GT in the fixed first-camera reference.'
        else:
            text = ('Mean L2 and recorded worker times. Historical timing boundaries and instrumentation differ, '
                    'so these observations do not establish a pure ICP speedup or statistical significance.')
        captions.append('### '+name+'\n\n'+text+'\n')
    (destination/'figure_captions.md').write_text('# Bonus figure captions\n\n'+'\n'.join(captions))
    write(destination/'manifest.json', dict(figures=manifest,
        captions_sha256=sha(destination/'figure_captions.md'), source_script_sha256=sha(Path(__file__)),
        reconstruction_repeated=False, source_map_or_pose_modified=False,
        draft_note='Original analysis 3D drafts retained; use these four label-repaired report figures.'))
    print('Report assets: '+str(destination))


if __name__ == '__main__':
    render()
