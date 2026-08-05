# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 21:02:03 2026

@author: Erin
"""

import numpy as np
import os
import subprocess
import time
import pyacvd
from pyvistaqt import BackgroundPlotter
import pyvista as pv

def run_bcpd(source_mesh, #the source mesh (or reference mesh)
             target_mesh, #the target mesh (for target geometry)
             bcpd, #path to BCPD executable
             args=None, #arguments for executable
             temp_dir=""):
    
    # write out points as temporary X and Y files 
    X = np.asarray(target_mesh.points, dtype=np.float64, order='C') #[rand_idxs_target, :]
    Y = np.asarray(source_mesh.points, dtype=np.float64, order='C') #[rand_idxs_source, :]
    x_file = 'X_temp.txt'
    y_file = 'Y_temp.txt'    

    np.savetxt(os.path.join(temp_dir,x_file),X,delimiter='\t')
    np.savetxt(os.path.join(temp_dir,y_file),Y,delimiter='\t')
    
    #CPD Parameters - default if none are provided
    if args is None:
        args = ['-w0.01', #omega
                '-b0.5', #beta
                '-l200', #lambda
                '-g0.1', #gamma
                '-ux', 
                '-K70', #K Nystrom samples for computing G
                '-J300', #J Nystrom samples for computing P
                '-c1e-6', #c
                '-p', #KD-tree serach is turned on
                '-f0.3',
                '-h', #
                '-r1', #seed for repeatibility 
                ]
    
    commands = [bcpd] + ['-x' + x_file] + ['-y' + y_file] +  args + ['-syex']
    
    #Execution
    print('Working on BCPD registration...')
    start_time = time.perf_counter()
    result = subprocess.run(commands,cwd=temp_dir,capture_output=True, text=True)
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.6f} seconds")
    
    #VISUALIZE MONKEY POINTS
    x_points= np.loadtxt(os.path.join(temp_dir,x_file),delimiter='\t')
    y_points= np.loadtxt(os.path.join(temp_dir,y_file),delimiter='\t')

    #load deformed mesh (output_y)
    def_points= np.loadtxt(os.path.join(temp_dir,'output_y.txt'),delimiter='\t')    
    deformed_mesh = source_mesh.copy()
    deformed_mesh.points = def_points
    
    #load corresponding mesh (output_x)
    cor_points = np.loadtxt(os.path.join(temp_dir,'output_x.txt'),delimiter='\t')
    corresp_mesh = source_mesh.copy()
    corresp_mesh.points = cor_points
    
    return deformed_mesh,corresp_mesh
    
def compute_mean_mesh(meshes, #list of PyVista Meshes that have same number of vertices
                      resample_pts = None): #Number of points to resample to
    
    num_pts = np.array(meshes[0].points).shape[0]
    all_coords = np.zeros((len(meshes),num_pts*3))
    
    #Add individuals to dataset
    for i, mesh in enumerate(meshes):
        points = np.array(mesh.points)
        
        all_coords[i,:] = points.reshape((-1,num_pts*3))
        
    #Compute mean coords and reshape
    mean_coords = np.nanmean(all_coords,axis=0).reshape((num_pts,3))
        
    #make new mesh from arbitrary copy (to preserve connections)
    mean_mesh = meshes[0].copy()    
    mean_mesh.points = mean_coords
    
    #resample points for uniform spaciong
    mean_mesh.acvd.remesh(n_clusters=resample_pts,
                          subdivide=3)
    
    return mean_mesh

def plot_assess_registered_meshes(registered_mesh, #mesh deformed from ref_mesh
                                  original_mesh, #original (target) mesh
                                  ref_mesh): #reference (mean) mesh
    
    #Calculate surface-to-surface distances (from registered mesh)
    _ = registered_mesh.compute_implicit_distance(original_mesh,inplace=True)
    #Calculate surface-to-surface distances (from original mesh)
    _ = original_mesh.compute_implicit_distance(registered_mesh,inplace=True)
    
    #Calculate ASSD for all points 
    dist_registered = np.absolute(np.array(registered_mesh.GetPointData().GetArray('implicit_distance')))
    dist_original = np.absolute(np.array(original_mesh.GetPointData().GetArray('implicit_distance')))
    all_dists = np.concatenate((dist_registered,dist_original))
    ASSD = np.mean(all_dists)
    
    #Create visual for each plotter
    p = BackgroundPlotter(shape=(2,2))
    
    #Plot errors (for each point on original mesh)
    p.subplot(0,0)
    p.add_mesh(mesh = registered_mesh,color=[0.5, 0.5, 0.5],style='wireframe',show_edges=True,edge_color='k',opacity=[0.01])
    p.add_mesh(mesh = original_mesh,scalars='implicit_distance',cmap='PRGn',clim=[-3,3])    
    p.add_text(
        f"Signed distances from points of original mesh, ASSD = {ASSD:.2f} mm",
        position="upper_left",
        font_size=12,
        color="black",
    )

    #Plot errors (for each point on registered mesh)
    p.subplot(0,1)
    p.add_mesh(mesh = registered_mesh,scalars='implicit_distance',cmap='PRGn',clim=[-3,3],copy_mesh=True)
    p.add_mesh(mesh = original_mesh,color=[0.5, 0.5, 0.5],style='wireframe',show_edges=True,edge_color='k',opacity=[0.01],copy_mesh=True)    
    p.add_text(
        f"Signed distances from points of registered mesh, ASSD = {ASSD:.2f} mm",
        position="upper_left",
        font_size=12,
        color="black",
    )
    
    #pick 20 random points to visualize correspondence
    rng = np.random.default_rng()
    random_numbers = rng.integers(low=0, high=len(ref_mesh.points)-1, size=20)
    colours = np.random.rand(20,3)
    
    #Prepare for visualization in ref_mesh_pts
    ref_mesh_pts = ref_mesh.points[random_numbers]
    registered_mesh_pts = registered_mesh.points[random_numbers]   
    
    #Plot arbitrary points on mean mesh
    p.subplot(1,0)
    p.add_mesh(mesh = ref_mesh,color=[0.5, 0.5, 0.5],copy_mesh=True) 
    p.add_points(points = ref_mesh_pts,scalars=colours, rgba=True,point_size=6,render_points_as_spheres=True)
    p.add_text(
        "Random points on reference mesh",
        position="upper_left",
        font_size=12,
        color="black",
    )
    
    #Plot the SAME arbitrary points on reference mesh
    p.subplot(1,1)
    p.add_mesh(mesh = registered_mesh,color=[0.5, 0.5, 0.5],copy_mesh=True) 
    p.add_points(points = registered_mesh_pts,scalars=colours, rgba=True,point_size=6,render_points_as_spheres=True)
    p.add_text(
        "The same random points on registered mesh",
        position="upper_left",
        font_size=12,
        color="black",
    )
    
    return p