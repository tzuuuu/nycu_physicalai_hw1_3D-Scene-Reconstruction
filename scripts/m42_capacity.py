"""Streaming map capacity preflight; unprojection/voxel counts only, never registration/GT."""
import resource
import sys
from pathlib import Path
import numpy as np
import utils


def capacity(capture):
    intr,pairs,scale=utils._capture_inputs(str(capture),None)
    counts=[]
    for rgb_path,depth_path in pairs:
        rgb,depth=utils._read_rgbd(rgb_path,depth_path,scale)
        cloud=utils.depth_image_to_point_cloud(rgb,depth,intr['width'],intr['height'],intr['hfov'])
        reduced=cloud.voxel_down_sample(.05)
        counts.append(dict(frame=int(Path(depth_path).stem),points=len(reduced.points)))
        del cloud,reduced,rgb,depth
    total=sum(r['points'] for r in counts)
    # XYZ+RGB float64 is 48 B/point. Six full map allocations cover vector growth,
    # ceiling index/select temporaries and exported map; allow 1 GiB for runtime,
    # two registration frames, features, rendering, libraries and allocator slack.
    bound=total*48*6+2**30
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    return dict(per_frame=counts,uncropped_map_point_upper_bound=total,
        map_point_color_bytes=total*48,planning_bound_bytes=bound,
        observed_preflight_process_peak_bytes=peak,limit_bytes=3*2**30,
        passed=bound<3*2**30 and peak<2**30,
        method='Per-frame exact map-only .05 voxel counts, no transforms/GT/RANSAC/ICP; rigid transforms preserve count; ceiling crop can only remove points',
        limitation='Conservative engineering allocation budget, not an allocator proof; live 3 GiB sampled tree guard remains mandatory')
