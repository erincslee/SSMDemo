# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 17:48:05 2026

node_correspondence_1.py

From mesh data stored in a .pkl file, runs following steps to establish node correspondence:
    
    1) Initial rigid alignment using inertial (principal) axes
    2) Finer rigid alignment with iterative closest point (ICP)
    2) First round of Bayesian Coherent Point Drift (BCPD) to generate a mean mesh to be used as reference mesh.
    3) Second round of BCPD to establish better point correspondence using mean mesh.
    4) Visualizes reconstruction errors for correspondence.

@author: Erin Lee
"""

import os
import pickle
from utils import *
import numpy as np
import pyvista as pv
from pyvistaqt import BackgroundPlotter
from pathlib import Path
import pyacvd


# %% ------------------------------------------------------------------
# Edit file paths and editable arguments
# -----------------------------------------------------------------------

# **EDIT** Parent directory where demo files are stored
PARENT_DIR = "C:\\Users\\Erin\\Documents\\Research\\SSMDemo"

# **EDIT ** Path to BCPD executable and directory where temporary files will be written and read
bcpd = "C:\\Users\\Erin\\Documents\\GitHub\\bcpd\\win\\bcpd.exe"

#Path to where meshes are stored
INPUT_DIR = os.path.join(PARENT_DIR,"Bone Models")
input_meshes_fname = os.path.join(INPUT_DIR,'mesh_data_original.pkl')

#Output directory for saving files
OUTPUT_DIR =  os.path.join(PARENT_DIR,"Output")
temp_dir = os.path.join(OUTPUT_DIR,"temp BCPD files")

#Location of mean mesh to use for final round of BCPD (to read/write)
mean_mesh_fname = Path(os.path.join(OUTPUT_DIR,'BCPD Round 1','mean_mesh.stl'));
#If True, compute new mean mesh from initial BCPD round.
#If False, load old mean mesh to use for final round of BCPD
overwrite_mean = False

#Location of registered meshes to use for SSM
output_meshes_fname = Path(os.path.join(OUTPUT_DIR,'BCPD Final Round','registered_meshes.pkl'))
#Also save out transforms to go from scanner space to aligned space (in case you want to include alignment in model later)
output_transforms_fname= Path(os.path.join(OUTPUT_DIR,'BCPD Final Round','alignment_transforms.pkl'))

# %% ------------------------------------------------------------------
# Load and visualize original meshes
# -----------------------------------------------------------------------
with open(input_meshes_fname, 'rb') as file:
    trimesh_OG = pickle.load(file)
num_meshes = len(trimesh_OG)

#Generate random colours for visualization
colours = np.random.rand(num_meshes,3)

#Loop through and convert to pyvista mesh
meshes_OG = []
p1 = BackgroundPlotter(title="1: Original Meshes")
print(f'Loading original meshes.')
for i,mesh_OG in enumerate(trimesh_OG):
    n_pts_OG = len(mesh_OG['vertices'])
    print(f'    Mesh {i} has {n_pts_OG} vertices.')
    meshes_OG.append(pv.make_tri_mesh(mesh_OG['vertices'], mesh_OG['faces']))
    p1.add_mesh(meshes_OG[i],color=colours[i,])

# %% ------------------------------------------------------------------
# Resample meshes (if desired)
# -----------------------------------------------------------------------

#Meshes straight out of segmentation software can be very large.
#Here, we use ACVD algorithm to resample surface to desired number of points
n_pts = 20000; #Using 20k for scapula
print(f'Resampling all meshes to {n_pts} vertices.')
meshes_resampled = []
for i,mesh in enumerate(meshes_OG):
    mesh_resampled = mesh.acvd.remesh(n_clusters = n_pts,
                                      subdivide=3)
    meshes_resampled.append(mesh_resampled)

# %% ------------------------------------------------------------------
# Perform rough initial rigid alignment 
# -----------------------------------------------------------------------

#Roughly align meshes by inertial axes
meshes_roughAligned = []
transforms = []
p2 = BackgroundPlotter(title="2: Meshes Roughly Aligned by Inertial Axes")
for i,mesh in enumerate(meshes_resampled):
    mesh_inertia, matrix_inertia = mesh.align_xyz(return_matrix=True)
    p2.add_mesh(mesh_inertia,color=colours[i,])
    #save aligned mesh and transform
    meshes_roughAligned.append(mesh_inertia)
    transforms.append(matrix_inertia)

# %% ------------------------------------------------------------------
# Perform iterative closest point for finer rigid alignment
# -----------------------------------------------------------------------

#We will arbitrarily use the first mesh as the reference mesh for rigid alignment
meshes_ICPAligned = []
p3 = BackgroundPlotter(title="3: Meshes Aligned with ICP")
for i,mesh in enumerate(meshes_roughAligned):
    
    if i == 0: #if first mesh, just save it to lsit
        meshes_ICPAligned.append(mesh)
    else: #align ALL other meshes to reference mesh
        mesh_ICP, matrix_ICP = mesh.align(
            target=meshes_ICPAligned[0],
            max_landmarks=100,
            max_iterations=100,
            return_matrix=True)
        p3.add_mesh(mesh_ICP,color=colours[i,])
        
        #save ICP mesh
        meshes_ICPAligned.append(mesh)
        
        #update transform to go from scanner space to new location
        transforms[i] = matrix_ICP @ transforms[i]

# %% ------------------------------------------------------------------

# Compute Mean Mesh (Reference Mesh)
# Perform (1st round) non-rigid registration with Bayesian Coherent Point Drift 

#For this first round, we won't worry about refining the parameters. 
#We are doing this round purely to get a better estimate of a mean shape to use
#as reference in the next round. (Ideally, you would first try to identify the 
#individual closest to the mean)

# -----------------------------------------------------------------------

if overwrite_mean is True:
    
    meshes_BCPDinit = []
    for i,mesh in enumerate(meshes_ICPAligned):
        
        print(f'Working on mesh {i} of {num_meshes}:')
        
        if i == 0: #if first mesh, just save it to list
            meshes_BCPDinit.append(mesh)
        else: #morph first mesh to match geometry of all other meshes
    
            #set parameters for BCPD
            args = ['-w0.01', #omega
                    '-b0.5', #beta
                    '-l200', #lambda
                    '-g0.5', #gamma
                    '-ux', 
                    '-K50', #K Nystrom samples for computing G
                    '-J100', #J Nystrom samples for computing P
                    '-c1e-6', #c
                    '-p', #KD-tree serach is turned on
                    '-f0.3',
                    '-h', #
                    '-r1', #seed for repeatibility 
                    ]
        
            #Run BCPD
            deformed_mesh, corresp_mesh = run_bcpd(source_mesh = meshes_ICPAligned[0], #the source mesh (or reference mesh)
                                                      target_mesh = mesh, #the target mesh (for target geometry)
                                                      bcpd=bcpd, #path to BCPD executable
                                                      args=args, #arguments for executable
                                                      temp_dir=temp_dir)
    
            meshes_BCPDinit.append(deformed_mesh)
            
    #Now, calculate mean mesh to use as reference for next round
    #This function calculates the mean coordinates then resamples the surface for uniform triangle size
    mean_mesh = compute_mean_mesh(meshes_BCPDinit)
    
    p4 = BackgroundPlotter(title="4: Mean Mesh from First round of ICP after remeshing")
    p4.add_mesh(mean_mesh,style="wireframe")
    
    #Save the 
    mean_mesh_fname.parent.mkdir(parents=True, exist_ok=True)
    mean_mesh.save(filename = mean_mesh_fname)

else: #If loading old mesh

    mean_mesh = pv.read(mean_mesh_fname)
    
# %% ------------------------------------------------------------------
# Perform (2st round) non-rigid registration with Bayesian Coherent Point Drift 

#For this final round, we will use the new mean mesh as the reference (source) mesh
#We will again use the ICP-aligned meshes as the target meshes
# -----------------------------------------------------------------------

meshes_BCPDfinal = []
for i,mesh in enumerate(meshes_ICPAligned):
    
    print(f'Working on mesh {i} of {num_meshes}:')
    
    #set parameters for BCPD
    args = ['-w0.01', #omega
            '-b0.5', #beta
            '-l200', #lambda
            '-g0.1', #gamma
            '-ux', 
            '-K150', #K Nystrom samples for computing G
            '-J300', #J Nystrom samples for computing P
            '-c1e-6', #c
            '-p', #KD-tree serach is turned on
            '-f0.3',
            '-h', #
            '-r1', #seed for repeatibility 
            ]

    #Run BCPD
    deformed_mesh, corresp_mesh = run_bcpd(source_mesh = mean_mesh, #the source mesh (or reference mesh)
                                              target_mesh = mesh, #the target mesh (for target geometry)
                                              bcpd=bcpd, #path to BCPD executable
                                              args=args, #arguments for executable
                                              temp_dir=temp_dir)
    #append deformed mesh
    meshes_BCPDfinal.append(deformed_mesh)
    
    p = plot_assess_registered_meshes(registered_mesh = deformed_mesh, #mesh deformed from ref_mesh
                                      original_mesh = mesh, #original (target) mesh
                                      ref_mesh = mean_mesh)
    
#Save the deformed meshes for future use in SSM
output_meshes_fname.parent.mkdir(parents=True, exist_ok=True)
with open(output_meshes_fname, "wb") as f:
    pickle.dump(meshes_BCPDfinal, f)

#Also save the transforms if wanting to save alignment
output_transforms_fname.parent.mkdir(parents=True, exist_ok=True)
with open(output_transforms_fname, "wb") as f:
    pickle.dump(transforms, f)
