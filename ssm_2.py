# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 08:09:53 2026

ssm_2.py

From corresponding meshes output from "node_correspondence_1", 
runs following steps to create statistical shape model:
    
    1) Initial rigid alignment using inertial (principal) axes
    2) Finer rigid alignment with iterative closest point (ICP)
    2) First round of Bayesian Coherent Point Drift (BCPD) to generate a mean mesh to be used as reference mesh.
    3) Second round of BCPD to establish better point correspondence using mean mesh.
    4) Visualizes reconstruction errors for correspondence.


@author: Erin Lee, with snippets from Allison Clouthier's Stanford Mobilize Webinar Series Google Collab
"""

# %% ------------------------------------------------------------------
# Edit file paths and editable arguments
# -----------------------------------------------------------------------

