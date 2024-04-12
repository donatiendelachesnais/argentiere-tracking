import os, sys
import numpy as np

sys.path.append('PyTrx/')
from PyTrx.CamEnv import CamEnv
from PyTrx.Velocity import Velocity, Homography
from PyTrx.FileHandler import writeHomogFile, writeVeloFile, writeVeloSHP, writeCalibFile
from PyTrx.Utilities import plotVeloPX, plotVeloXYZ, interpolateHelper, plotInterpolate

cameraenvironment = CamEnv('camdata.txt')