# Statistical Shape Modelling Demo in Python 
By Erin Lee, 2026

This is working demo for generating a surface-based statistical shape model from input meshes in Python.

The visualization tools are specifically written to work in Spyder. However, they could be adapted for Jupyter notebook or Google Collab in the future.

The demo is constructed of 3 parts, split in to 3 scripts. 

* <b>Step 0: compile_input_meshes_0.py </b> 
  *   From STL files, compile all mesh information into a single pickle (.pkl) file.

* <b>Step 1: node_correspondence_1.py </b> 
  *   Performs rigid alignment (with ICP) then then non-rigid (morphable) registration with BCPD.
 
* <b>Step 2: ssm_2.py </b> 
  *   [In progress] Performs Procrustes alignment and PCA to generate SSM

## Installation

Clone this repository, then create and activate a new conda environment to install requirements.

```bash
cd [location of repository]
conda create --name ssm --file requirements.txt
```

Clone the Bayesian Coherent Point Drift (BCPD) package (https://github.com/ohirose/bcpd) and note the location of the package.

## Step 0
