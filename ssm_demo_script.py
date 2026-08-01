# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 17:48:05 2026

ssm_demo_script.py

From shape data stored in a .pkl file, runs following steps to generate a 
statistical shape model:
    
    1) Initial (rough) registration with iterative closest point (ICP)
    2) First round of Bayesian Coherent Point Drift (BCPD) to establish point
    correspondence. Uses random mesh as reference.
    3) Second round og BCPD to establish better point correspondence. 
    4) Visualizes reconstruction errors for correspondence.
    5) Performs Procrustes analysis to scale, align, and centre meshes.
    6) Performs PCA and animates PCs

@author: Erin Lee, using pieces from Allison Clouthier's Stanford Mobilize Google 
Collab tutorial
"""

import os
import pickle
from utils import *
import numpy as np
import pyvista as pv
from pyvistaqt import BackgroundPlotter

# %% ------------------------------------------------------------------
# Edit file paths
# -----------------------------------------------------------------------

#Path to where meshes are stored
INPUT_DIR = 'C:\\Users\\Erin\\Documents\\Research\\SSMDemo\\Bone Models'
INPUT_PICKLE = os.path.join(INPUT_DIR,'mesh_data_original.pkl')

#Output directory for saving files
OUTPUT_DIR = "C:\\Users\\Erin\\Documents\\Research\\SSMDemo\\Output"
save_intermediate_steps = True

#Path to BCPD executable and directory where temporary files will be written and read
bcpd = "C:\\Users\\Erin\\Documents\\GitHub\\bcpd\\win\\bcpd.exe"
temp_dir = os.path.join(OUTPUT_DIR,"temp BCPD files")

# %% ------------------------------------------------------------------
# Load and visualize original meshes
# -----------------------------------------------------------------------
 
INPUT_DIR = 'C:\\Users\\Erin\\Documents\\Research\\SSMDemo\\Bone Models'
INPUT_PICKLE = os.path.join(INPUT_DIR,'mesh_data_original.pkl')

with open(INPUT_PICKLE, 'rb') as file:
    trimesh_OG = pickle.load(file)
num_meshes = len(trimesh_OG)

#Generate random colours for visualization
colours = np.random.rand(num_meshes,3)

#Loop through and convert to pyvista mesh
meshes_OG = []
p1 = BackgroundPlotter(title="1: Original Meshes")
for i,mesh_OG in enumerate(trimesh_OG):
    meshes_OG.append(pv.make_tri_mesh(mesh_OG['vertices'], mesh_OG['faces']))
    p1.add_mesh(meshes_OG[i],color=colours[i,])

# %% ------------------------------------------------------------------
# Perform rough initial rigid alignment 
# -----------------------------------------------------------------------

#Roughly align meshes by inertial axes
meshes_roughAligned = []
transforms = []
p2 = BackgroundPlotter(title="2: Meshes Roughly Aligned by Inertial Axes")
for i,mesh in enumerate(meshes_OG):
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
# Perform (1st round) non-rigid registration with Bayesian Coherent Point Drift 

#For this first round, we won't worry about refining the parameters. 
#We are doing this round purely to get a better estimate of a mean shape to use
#as reference in the next round. (Ideally, you would first try to identify the 
#individual closest to the mean)

# -----------------------------------------------------------------------
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
                '-J150', #J Nystrom samples for computing P
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
mean_mesh = compute_mean_mesh(meshes_BCPDinit)

p4 = BackgroundPlotter(title="4: Mean Mesh from First round of ICP")
p4.add_mesh(mean_mesh,style="wireframe")

#Save the 

mean_mesh.save(filename = os.path.join(OUTPUT_DIR,'BCPD Round 1','mean_mesh.stl'))

# %% ------------------------------------------------------------------
# Perform (2st round) non-rigid registration with Bayesian Coherent Point Drift 

#For this final round, we will use the new mean mesh as the reference (source) mesh

# -----------------------------------------------------------------------

