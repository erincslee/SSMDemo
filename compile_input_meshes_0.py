# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 17:48:05 2026

compile_input_meshes_0.py

Combines mesh data into a single .pkl file. Compiling open-access bone meshes 
available on the Queen's Borealis Dataverse (https://doi.org/10.5683/SP3/PKJDCL)
accompanying the paper by Lee et al. 2025 (doi: 10.1016/j.jbiomech.2025.112932) 

@author: Erin Lee
"""

import os
import pickle
import trimesh
import numpy as np
from pathlib import Path

# %% ------------------------------------------------------------------
# Edit file paths
# -----------------------------------------------------------------------
 
INPUT_DIR = 'C:\\Users\\Erin\\Documents\\Research\\SSMDemo\\Bone Models'
OUTPUT_PICKLE = os.path.join(INPUT_DIR,'mesh_data_original.pkl')
PATTERN = "*_Scapula.stl"

# %% ------------------------------------------------------------------
# Function to extract mesh info from a single STL
# -----------------------------------------------------------------------
 
#Only saving vertices and faces to reduce file size

def load_mesh_info(stl_path: Path) -> dict:
    """Load a single STL file and extract mesh info relevant to SSM."""
    mesh = trimesh.load(stl_path, process=False)
 
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(f"{stl_path.name} did not load as a single Trimesh object.")
 
    info = {
        "vertices": np.asarray(mesh.vertices),      # (N, 3)
        "faces": np.asarray(mesh.faces)             # (M, 3)
    }
    return info
 
# %% ------------------------------------------------------------------
# Find STL files
# -----------------------------------------------------------------------
 
input_dir = Path(INPUT_DIR)
output_pickle = Path(OUTPUT_PICKLE)
 
if not input_dir.is_dir():
    raise NotADirectoryError(f"Input directory not found: {input_dir}")
 
stl_files = sorted(input_dir.glob(PATTERN))
 
if not stl_files:
    raise FileNotFoundError(f"No files matching '{PATTERN}' found in {input_dir}")
 
print(f"Found {len(stl_files)} STL file(s) to load from {input_dir}")
 
# %% ------------------------------------------------------------------
# Load meshes
# -----------------------------------------------------------------------
 
mesh_data = []
for i, stl_path in enumerate(stl_files, start=1):
    print(f"  [{i}/{len(stl_files)}] Loading {stl_path.name} ...")
    try:
        info = load_mesh_info(stl_path)
        mesh_data.append(info)
    except Exception as e:
        print(f"    Failed to load {stl_path.name}: {e}")

# %% ------------------------------------------------------------------
# Save to pickle
# -----------------------------------------------------------------------
 

output_pickle.parent.mkdir(parents=True, exist_ok=True)
with open(output_pickle, "wb") as f:
    pickle.dump(mesh_data, f)
 
print(f"\nSaved mesh info for {len(mesh_data)} mesh(es) to {output_pickle}")
 