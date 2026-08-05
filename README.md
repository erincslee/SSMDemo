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

## Step 0: Compile Input Meshes

For the purposes of this demo, I used meshes from an open-access dataset associated with the manuscript <i>Scapular kinematics and task specificity: The effect of load direction</i> by Lee et al. (2025). Humerus and scapula meshes are availabled on the Queen's University Borealis Dataverse (https://doi.org/10.5683/SP3/PKJDCL). 

This script loads the individual scapula meshes as .STL files, and saves them as a list in the pickle file, <b>"mesh_data_original.pkl"</b> which is included in this repo. 

The script <b>compile_input_meshes_0.py</b> is included to help you compile your own meshes. 

## Step 1: Node Correspondence 

Statistical shape models rely on anatomical correspondance. Meaning, the bones must be composed of the same number of vertices and connections as the template. Those vertices must also be anatomically corresponding. For example, if the inferior angle is point #100 on the template scapula, it must also be point #100 on any new scapula being used in the Main Demo. 

Below shows a simple example of two 2D face silhouettes. The "corresponding" faces are constructed of anatomically homologous vertices. (For example, Point #1 is the tip of the nose in both cases)

<img width="305" height="162" alt="image" src="https://github.com/user-attachments/assets/34f98cc6-05e7-4324-9fff-fe80d1c0f1a1" />  <img width="300" height="175" alt="image" src="https://github.com/user-attachments/assets/5291b826-f367-470f-a004-f5f58b35117c" />

Often, this is the most challenging aspect of generating an SSM. 

The script <b>node_correspondence_1.py</b> performs rigid alignment (to centre and align all meshes) then non-rigid registration with Bayesian Coherent Point Drift (to establish node correspondence). You will need to edit the filepaths and location of the BCPD executable to run this script.

### A) Original meshes are loaded and resampled

The original meshes are not aligned because their reference coordinate system is relative to the CT scanner, and positioning varies across participants. The meshes may be composed of a large number of vertices, which can slow down computation time. We therefore resample to a specific number of points (currently defaulted to 20k for the scapula).

<img width="253" height="261" alt="image" src="https://github.com/user-attachments/assets/7afd6813-6863-40ca-babb-5f8a43e1f1be" />

### B) Resampled meshes are roughly aligned according to inertial (principle) axes

The resampled meshes are then transformed into their inertial axes and centred. This achieves a rough rigid alignment. 

<img width="237" height="253" alt="image" src="https://github.com/user-attachments/assets/43744053-d5d6-45a0-a3fa-85236b7b68fe" />

### C) Meshes are aligned more finely with Iterative Closest Point (ICP) Algorithm

This finer alignment step attempts to minimize variability in node coordinates due to alignment. 

<img width="237" height="245" alt="image" src="https://github.com/user-attachments/assets/55425169-bd86-4704-acc4-4596d5090596" />

### D) An initial round of BCPD (non-rigid registration) is performed to establish a mean mesh. 

Non-rigid registration (node correspondence) is best if a mean mesh is used as the reference (template) mesh. To generate this reference mesh, we perform an initial round of BCPD to establish a mean mesh. This mean mesh is then resampled to have even triangle sizes.

You can choose to skip this step if you have already generated a mean mesh. (You can read it in the file instead).

<img width="292" height="287" alt="image" src="https://github.com/user-attachments/assets/6010c077-c99f-4c3f-9035-ee018d2fe67d" />

### E) A final, refined round of BCPD to generate final, corresponding meshes.

A final round of BCPD is performed with the mean mesh as the reference mesh. For each mesh in the dataset, the reference mesh will deform to best match the geometry of the target (original) mesh. 

<b>Important Note </b>: The non-rigid registration will produce two meshes:
   * The <b>*deformed mesh*</b>: the template mesh morphed to match the geometry of the input mesh.
   * The <b>*corresponding mesh*</b>: a mesh constructed from the corresponding vertices within the input mesh.

Choosing a mesh to use going forward (default: <b>*deformed*</b>):
   * The deformed mesh is smoother, but will have higher surface-to-surface errors because it is not using points directly from the original mesh.
   * The corresponding mesh can be technically more accurate, but small correspondence errors will lead to large discontinuous in the mesh. Particularly for the scapula, correspondence can be challenging on the blade, leading to "inside-out" portions of bone.
   * By default, this script visualizes and assesses the <b>*deformed mesh*</b> because it is a cleaner mesh.

For each mesh, a quality check is performed by visualizing reconstruction errors and calculating the Average Symmetric Surface Distance (ASSD). A window will appear with 4 subplots:
 * <b>Top left</b>: Distances visualized from points on the original mesh to the surface of the registered (reconstructed) mesh. The original mesh is coloured according to those distances (purple inside the bone and green outside fo the bone). The registered mesh is visualized as a wireframe.
 * <b>Top right</b>: Distances visualized from points on the registered mesh to the surface of the original mesh. The registered mesh is coloured according to those distances (purple inside the bone and green outside fo the bone). The original mesh is visualized as a wireframe.
 * <b>Bottom left</b>: 20 arbitrary points visualized on the reference (mean) mesh
 * <b>Bottom right</b>: The same 20 points visualized on the registered mesh, to assess how well homology was achieved. 

You will see that while the ASSD errors are low, <b>some of the registered meshes fail to capture geometry in challenging regions</b> (e.g. the coracoid and acromion). Here are some approaches that can help refine the registration:
 * Edit the BCPD parameters (https://github.com/ohirose/bcpd) for details.
 * Adjust the number of points comprising the meshes. Sometimes, it helps if the reference mesh has more vertices than the target meshes.
 * Try refining and/or quality checking the initial round of BCPD to get a better mean (reference) mesh.
 
 <img width="1312" height="828" alt="image" src="https://github.com/user-attachments/assets/5f081ca1-f2a8-4742-ba34-102d0c5e2306" />

### F: Final registered meshes and their transforms are exported.

The final, registered meshes are exported in a list as a pickle file. 
The transforms used for alignment are also exported, so they can be re-aligned later if you want to include alignment in your shape model. 
