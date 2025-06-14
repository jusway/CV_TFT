from pathlib import Path
class Config:
    # 当前路径
    cwd = Path(__file__).resolve().parent
    # 上一级路径
    parent = cwd.parent
    # 图片路径
    pictrue_dir= cwd/'pictures'
    # 阵容路径
    lineup_dir= parent/'阵容'

    output_idx=0
    point= 485,931
    h=135
    w=183
    move=201
    y_bias=0
