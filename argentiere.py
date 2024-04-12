import os, sys
import numpy as np

#import PyTrx modules
sys.path.append('PyTrx/')
from PyTrx.CamEnv import CamEnv
from PyTrx.Velocity import Velocity, Homography
from PyTrx.FileHandler import writeHomogFile, writeVeloFile, writeVeloSHP, writeCalibFile
from PyTrx.Utilities import plotVeloPX, plotVeloXYZ, interpolateHelper, plotInterpolate


#Define data output directory
destination = '../Examples/results/test_velocity1/'


#-----------------------   Create camera object   -----------------------------

#Define camera environment
cameraenvironment = CamEnv('camdata.txt')

#Optimise camera environment to refine camera pose
cameraenvironment.optimiseCamEnv('YPR')

#Report camera data and show corrected image
cameraenvironment.reportCamData()
cameraenvironment.showGCPs()
cameraenvironment.showPrincipalPoint()
cameraenvironment.showResiduals()
