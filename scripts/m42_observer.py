"""Read-only Python return observer for arbitrary N, full same-call map export."""
import json
from pathlib import Path
import resource
import runpy
import sys
import time
import traceback

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import utils
from scripts.m4_capture_check import sha
from scripts.m42_monitor import write, append


def expected_counts(n):
    if n < 1: raise ValueError('Capture must contain frames')
    return dict(frames=n,pairs=n-1,factors=2*n+6*(n-1))


def save_map(cloud, output):
    """np.save streams contiguous float64 vector views; no cloud-sized copy/zip buffer.

    The returned Open3D cloud remains alive until both writes complete.
    """
    output=Path(output)
    before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    started=time.perf_counter()
    arrays={}
    for name, vector in [('map_points',cloud.points),('map_colors',cloud.colors)]:
        array=np.asarray(vector)
        if array.dtype!=np.float64 or array.ndim!=2 or array.shape[1]!=3 or not array.flags.c_contiguous:
            raise RuntimeError('Unexpected Open3D export layout; no implicit large copy allowed')
        with (output/(name+'.npy')).open('xb') as f:
            np.save(f,array,allow_pickle=False)
        arrays[name]=dict(shape=list(array.shape),dtype=str(array.dtype),sha256=sha(output/(name+'.npy')))
    if arrays['map_points']['shape']!=arrays['map_colors']['shape']:
        raise RuntimeError('Map colors do not cover all points')
    after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result=dict(arrays=arrays,point_count=len(cloud.points),full_returned_map=True,
        sample_stride=1,coordinate_system='first captured camera; +X right +Y down +Z forward',
        map_only_down_voxel_m=.05,ceiling_crop='teacher remove_ceiling_points: Y > min(Y)+1m',
        export_s=time.perf_counter()-started,
        peak_rss_increase_bytes=max(0,after-before)*(1 if sys.platform=='darwin' else 1024),
        storage='separate uncompressed NPY files, NumPy contiguous views, streamed file writes')
    write(output/'map_summary.json',result)
    return result


class Observer:
    def __init__(self,output):
        self.output=Path(output)
        self.codes={name:getattr(utils,name).__code__ for name in
            ['reconstruct','_read_rgbd','preprocess_point_cloud','_global_registration',
             'local_icp_algorithm','visualize_and_evaluate']}
        self.events=[]; self.transforms=[]; self.calls=0; self.poses=[np.eye(4)]
        self.started=None; self.elapsed=None; self.overhead_s=0.

    def __call__(self,frame,event,value):
        code=frame.f_code
        if code not in self.codes.values(): return
        start=time.perf_counter()
        parent=frame.f_back
        pipeline=parent is not None and parent.f_code is self.codes['reconstruct']
        if event=='call' and code is self.codes['reconstruct']:
            self.calls+=1; self.started=time.perf_counter()
            local=frame.f_locals
            write(self.output/'actual_reconstruct_arguments.json',
                {k:str(local[k]) if k=='data_root' else local[k] for k in
                 ['data_root','version','voxel_size','build_cloud','frames','down_voxel','registration_seed']})
        if pipeline and code is self.codes['_read_rgbd'] and event=='call':
            append(self.output/'progress.jsonl',dict(kind='frame_begin',current=parent.f_locals['stem'],unix=time.time()))
        if pipeline and code is self.codes['_global_registration'] and event=='call':
            local=parent.f_locals
            append(self.output/'progress.jsonl',dict(kind='pair_begin',previous=local['prev_stem'],
                current=local['stem'],unix=time.time()))
        if event=='return' and value is not None:
            if pipeline and code is self.codes['preprocess_point_cloud']:
                local=parent.f_locals
                row=dict(kind='frame',stem=local['stem'],raw_point_count=len(local['pcd'].points),
                    point_yield=len(value[0].points))
                self.events.append(row); append(self.output/'events.jsonl',row)
                append(self.output/'progress.jsonl',dict(kind='frame_preprocessed',current=local['stem'],unix=time.time()))
            elif pipeline and code is self.codes['_global_registration']:
                local=parent.f_locals
                append(self.output/'ransac_returns.jsonl',dict(previous=local['prev_stem'],current=local['stem'],
                    transformation=np.asarray(value.transformation).tolist(),fitness=float(value.fitness),
                    rmse=float(value.inlier_rmse),correspondences=len(value.correspondence_set)))
            elif pipeline and code is self.codes['local_icp_algorithm']:
                local=parent.f_locals; coarse=local['coarse_result']
                row=dict(kind='pair',prev_stem=local['prev_stem'],stem=local['stem'],
                    coarse_fitness=float(coarse.fitness),coarse_rmse=float(coarse.inlier_rmse),
                    coarse_correspondences=len(coarse.correspondence_set),icp_fitness=float(value.fitness),
                    icp_rmse=float(value.inlier_rmse),icp_correspondences=len(value.correspondence_set))
                self.events.append(row); append(self.output/'events.jsonl',row)
                transform=dict(row,trans_init=np.asarray(local['trans_init']).tolist(),
                    icp_transformation=np.asarray(value.transformation).tolist(),direction='current->previous',
                    accepted_by_core=bool(len(coarse.correspondence_set)>0 and coarse.fitness>0
                        and np.isfinite(coarse.fitness) and np.isfinite(coarse.inlier_rmse)
                        and np.isfinite(coarse.transformation).all() and len(value.correspondence_set)>0
                        and value.fitness>0 and np.isfinite(value.fitness) and np.isfinite(value.inlier_rmse)
                        and np.isfinite(value.transformation).all()))
                self.transforms.append(transform); append(self.output/'transforms.jsonl',transform)
                if transform['accepted_by_core']:
                    self.poses.append(self.poses[-1] @ np.asarray(value.transformation))
                    append(self.output/'accepted_poses.jsonl',dict(stem=local['stem'],pose=self.poses[-1].tolist()))
            elif code is self.codes['reconstruct']:
                self.elapsed=time.perf_counter()-self.started
                cloud,positions=value
                poses=np.asarray(self.poses)
                np.testing.assert_allclose(poses[:,:3,3],positions,rtol=0,atol=1e-12)
                saved_arrays={}
                for name,array in [('camera_poses',poses),('positions',positions),
                    ('pairwise_icp',np.asarray([r['icp_transformation'] for r in self.transforms]).reshape(-1,4,4)),
                    ('pairwise_ransac',np.asarray([r['trans_init'] for r in self.transforms]).reshape(-1,4,4))]:
                    with (self.output/(name+'.npy')).open('xb') as f: np.save(f,array,allow_pickle=False)
                    saved_arrays[name]=dict(dtype=str(array.dtype),shape=list(array.shape),sha256=sha(self.output/(name+'.npy')))
                write(self.output/'trajectory_metadata.json',dict(arrays=saved_arrays,
                    frame_indices=[int(Path(d).stem) for r,d in frame.f_locals['pairs']],
                    reference='first original captured camera; +X right +Y down +Z forward',
                    camera_poses='4x4 current camera to first camera; cumulative right products of same-run ICP returns',
                    positions='same-call utils.reconstruct return, camera centers',
                    pairwise_direction='current->previous',
                    pairwise_source='same-run RANSAC initial and ICP final returns; frame indices in transforms.jsonl',
                    capture=str(frame.f_locals['data_root'])))
                save_map(cloud,self.output)
            elif code is self.codes['visualize_and_evaluate']:
                write(self.output/'official_evaluation.json',dict(mean_l2_raw_m=float(value)))
        self.overhead_s+=time.perf_counter()-start


def execute_cli(experiment,output):
    output=Path(output); output.mkdir(exist_ok=False)
    if sys.getprofile() is not None: raise RuntimeError('Existing profiler')
    observer=Observer(output)
    prior=sys.argv
    sys.argv=[str(ROOT/'reconstruct.py'),'--experiment',str(experiment),'--version','open3d',
        '--voxel-size','0.05','--seed','0','--down-voxel','0.05','--no-vis']
    status='failed'
    try:
        sys.setprofile(observer)
        runpy.run_path(str(ROOT/'reconstruct.py'),run_name='__main__')
        status='official_cli_returned'
    except BaseException:
        (output/'failure.traceback.txt').write_text(traceback.format_exc())
        raise
    finally:
        sys.setprofile(None); sys.argv=prior
        write(output/'observer_summary.json',dict(status=status,reconstruct_calls=observer.calls,
            frame_events=sum(e['kind']=='frame' for e in observer.events),pair_events=len(observer.transforms),
            valid_transform_pose_prefix_frames=len(observer.poses) if observer.events else 0,
            full_processed_frames=len(observer.poses) if status=='official_cli_returned' else None,
            prefix_note='Pose prefix from finite positive-support returned transforms; not a claim that all map integration steps completed',
            reconstruction_s_with_observation=observer.elapsed,
            return_observer_overhead_s=observer.overhead_s))
    return observer
