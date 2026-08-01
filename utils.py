# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 21:02:03 2026

@author: Erin
"""

import numpy as np
import os
import subprocess
import time

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
    
    #Plot result
    
    # pl = pv.Plotter(notebook=False)
    # pl.add_points(x_points,
    #           style = 'points',
    #           render_points_as_spheres=True,
    #           point_size=3,
    #           color = 'blue')
    # # pl.add_points(y_points,
    # #           style = 'points',
    # #           render_points_as_spheres=True,
    # #           point_size=3,
    # #           color = 'red')
    # pl.add_points(aligned_x,
    #           style = 'points',
    #           render_points_as_spheres=True,
    #           point_size=5,
    #           color = 'orange')   
    # pl.add_points(new_points,
    #           style = 'points',
    #           render_points_as_spheres=True,
    #           point_size=5,
    #           color = 'black')   
    # pl.show()

def compute_mean_mesh(meshes): #list of PyVista Meshes that have same number of vertices
    
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
    
    return mean_mesh