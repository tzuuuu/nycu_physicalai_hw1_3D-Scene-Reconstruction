"""僅讀取已完成診斷的轉換與 RGB-D，製作失敗點細節；不執行配準。"""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import m3_diagnose as m
import numpy as np
import cv2


def details(run, analysis, output):
    run, analysis = Path(run), Path(analysis)
    check = json.loads((run/'comparison.json').read_text())
    if not check['baseline_equivalent'] or not check['protected_files_unchanged']:
        raise RuntimeError('Only analyze a verified matched run')
    output = m.fresh_output(output)
    frames = list(csv.DictReader((analysis/'frames.csv').open()))
    pairs = list(csv.DictReader((analysis/'pairs.csv').open()))
    transforms = [json.loads(s) for s in (run/'transforms.jsonl').read_text().splitlines()]
    poses = np.load(analysis/'poses_offline.npz')
    intrinsics, paths, scale = m.utils._capture_inputs(str(m.DATA), None)
    mapping = {int(Path(d).stem):(rgb,d) for rgb,d in paths}
    measurements, clouds = [], {}
    for stem in [20,24,48,49,52,55,70,71,100,101,102,103,104,105,114,116,117,133,134,147,148,151]:
        rgb,depth = m.utils._read_rgbd(*mapping[stem],scale)
        cloud = m.utils.depth_image_to_point_cloud(rgb,depth,**intrinsics).voxel_down_sample(.05)
        points = np.asarray(cloud.points)
        eigenvalues = np.linalg.eigvalsh(np.cov(points.T))
        grey = cv2.cvtColor(rgb,cv2.COLOR_BGR2GRAY)
        measurements.append({'frame':stem,'voxel_count':len(points),
                             'valid_depth_fraction':float(np.mean(depth>0)),
                             'mean_grey_0_255':float(grey.mean()),
                             'dark_pixel_fraction_below30':float(np.mean(grey<30)),
                             'bright_pixel_fraction_atleast250':float(np.mean(grey>=250)),
                             'spatial_covariance_smallest_fraction':float(eigenvalues[0]/eigenvalues.sum())})
        clouds[stem] = points.copy()
    m.write_csv(output/'image_geometry_measurements.csv',measurements)
    prefix = np.load(m.ROOT/'research_outputs/m2_20261118_mapvoxel_01/frames_20/positions.npy')
    prediction = np.load(run/'positions.npy')
    errors = np.array([float(r['l2_m']) for r in frames])
    item = next(t for t in transforms if t['stem']==104)
    gt = np.linalg.inv(poses['gt'][102]) @ poses['gt'][103]
    initial,final=np.array(item['trans_init']),np.array(item['icp_transformation'])
    m.dump(output/'detail_summary.json',{
        'source_run':str(run),'source_analysis':str(analysis),
        'kind':'offline_evaluation_only_no_registration_or_intervention',
        'prefix20_max_position_difference_m':float(np.abs(prefix-prediction[:20]).max()),
        'sum_l2_fraction_frames104_191':float(errors[103:].sum()/errors.sum()),
        'maximum_l2_frame':int(frames[int(np.argmax(errors))]['frame']),
        'maximum_l2_m':float(errors.max()),
        'pair103_104':{'coarse':initial.tolist(),'icp':final.tolist(),'gt_for_evaluation_only':gt.tolist(),
                       **m.pair_metrics(final,gt,initial)},
        'note':'PCA fraction is spatial flatness, not an ICP Hessian or proof of ambiguity.'})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(4,1,figsize=(12,11),constrained_layout=True)
    keys=[('l2_m','Camera-centre L2 (m)'),('cumulative_orientation_error_deg','Accumulated orientation error (deg)')]
    for ax,(key,label) in zip(axes[:2],keys):
        subset=[r for r in frames if 95<=int(r['frame'])<=120]
        ax.plot([int(r['frame']) for r in subset],[float(r[key]) for r in subset],'.-')
        ax.set_ylabel(label)
    for ax,key,label in zip(axes[2:],['relative_translation_error_m','relative_rotation_error_deg'],['Local translation error (m)','Local rotation error (deg)']):
        subset=[p for p in pairs if 95<=int(p['current'])<=120]
        ax.plot([int(p['current']) for p in subset],[float(p[key]) for p in subset],'.-')
        ax.set_yscale('log'); ax.set_ylabel(label)
    for ax in axes:
        ax.axvline(104,color='red',linestyle='--',label='103 -> 104')
        ax.axvline(115,color='grey',linestyle=':',label='Translation resumes at 115')
        ax.set_xlabel('Current frame stem'); ax.grid(alpha=.3)
    axes[0].legend(); fig.savefig(output/'onset_95_120.png',dpi=150); plt.close(fig)
    # 只把已保存的變換套用在兩張點雲上供誤差定位；GT 沒有送入任何配準。
    fig,axes=plt.subplots(2,3,figsize=(15,9),constrained_layout=True)
    target,source=clouds[103],clouds[104]
    transformed=[source@t[:3,:3].T+t[:3,3] for t in [initial,final,gt]]
    all_points=np.concatenate([target]+transformed)
    for col,(name,points) in enumerate(zip(['Saved RANSAC','Saved ICP','GT (offline evaluation only)'],transformed)):
        for row,(a,b) in enumerate([(0,1),(2,1)]):
            ax=axes[row,col]
            ax.scatter(target[::3,a],target[::3,b],s=2,alpha=.3,label='Target 103',color='steelblue')
            ax.scatter(points[::3,a],points[::3,b],s=2,alpha=.3,label='Source 104 transformed',color='darkorange')
            ax.set(xlabel='XYZ'[a]+' (m)',ylabel='XYZ'[b]+' (m)',title=name,
                   xlim=(all_points[:,a].min()-.1,all_points[:,a].max()+.1),
                   ylim=(all_points[:,b].min()-.1,all_points[:,b].max()+.1))
            ax.set_aspect('equal'); ax.invert_yaxis(); ax.grid(alpha=.2)
    axes[0,0].legend(markerscale=3,fontsize=8)
    fig.suptitle('103 -> 104: identical raw RGB-D and fixed 0.05 m voxel; no re-registration')
    fig.savefig(output/'pair103_104_cloud_projections.png',dpi=150); plt.close(fig)
    print(json.dumps(measurements,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True)
    parser.add_argument('--analysis',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    details(args.run,args.analysis,args.output)
