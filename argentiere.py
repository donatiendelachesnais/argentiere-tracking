import os, sys
import numpy as np

#import PyTrx modules
sys.path.append('PyTrx/')
from PyTrx.CamEnv import CamEnv
from PyTrx.Velocity import Velocity, Homography
from PyTrx.FileHandler import writeHomogFile, writeVeloFile, writeVeloSHP, writeCalibFile
from PyTrx.Utilities import plotVeloPX, plotVeloXYZ, interpolateHelper, plotInterpolate

#-------------------------   Map data sources   -------------------------------
pwd = os.getcwd()
mask = None
invmask = None
imgs = 'Images/*.JPG'
#Define data output directory
destination = pwd + r'\\results\\'


#-----------------------   Create camera object   -----------------------------

#Define camera environment
cameraenvironment = CamEnv('camdata.txt')

#Optimise camera environment to refine camera pose
cameraenvironment.optimiseCamEnv('YPR',show=True)
cameraenvironment.optimiseCamEnv('INT',show=True)

#Report camera data and show corrected image
cameraenvironment.reportCamData()
cameraenvironment.showGCPs()
cameraenvironment.showPrincipalPoint()
cameraenvironment.showResiduals()


#----------------------   Calculate homography   ------------------------------

#Set homography parameters
hmethod='sparse'                #Method
hgwinsize=(25,25)               #Tracking window size
hgback=1.0                      #Back-tracking threshold
hgmax=50000                     #Maximum number of points to seed
hgqual=0.1                      #Corner quality for seeding
hgmind=5.0                      #Minimum distance between seeded points
hgminf=4                        #Minimum number of seeded points to track

#Set up Homography object
homog = Homography(imgs, cameraenvironment, invmask, calibFlag=True, 
                band='L', equal=True)

#Calculate homography
hgout = homog.calcHomographies([hmethod, [hgmax, hgqual, hgmind], [hgwinsize, 
                                hgback, hgminf]])

    
#----------------------   Calculate velocities   ------------------------------

#Set velocity parameters
vmethod='sparse'                #Method
vwinsize=(25,25)                #Tracking window size
bk = 1.0                        #Back-tracking threshold  
mpt = 50000                     #Maximum number of points to seed
ql = 0.1                        #Corner quality for seeding
mdis = 5.0                      #Minimum distance between seeded points
mfeat = 4                       #Minimum number of seeded points to track

#Set up Velocity object
velo=Velocity(imgs, cameraenvironment, hgout, mask, calibFlag=True, 
              band='L', equal=True) 

velocities = velo.calcVelocities([vmethod, [mpt, ql, mdis], [vwinsize, bk, 
                                  mfeat]])                                   
                                    
xyzvel=[item[0][0] for item in velocities] 
xyz0=[item[0][1] for item in velocities]
xyz1=[item[0][2] for item in velocities]
xyzerr=[item[0][3] for item in velocities]
uvvel=[item[1][0] for item in velocities]
uv0=[item[1][1] for item in velocities] 
uv1=[item[1][2] for item in velocities]
uv1corr=[item[1][3] for item in velocities]


#---------------------------  Export data   -----------------------------------

print('\n\nWRITING DATA TO FILE')

#Write out camera calibration info to .txt file
target1 = destination +  'CAM5_calib.txt'
matrix, tancorr, radcorr = cameraenvironment.getCalibdata()
writeCalibFile(matrix, tancorr, radcorr, target1)

#Write out velocity data to .csv file
target2 = destination + 'velo_output.csv'
imn = velo.getImageNames()
writeVeloFile(xyzvel, uvvel, hgout, imn, target2) 

#Write homography data to .csv file
target3 = destination + 'homography.csv'
writeHomogFile(hgout, imn, target3)

#Write points to shp file
target4 = destination + 'shpfiles/'     #Define file destination
if not os.path.exists(target4):
    os.makedirs(target3)                #Create file destination
proj = 32633                            #ESPG:32633 is projection WGS84
writeVeloSHP(xyzvel, xyzerr, xyz0, imn, target4, proj)       #Write shapefile

  
#----------------------------   Plot Results   --------------------------------

print('\n\nPLOTTING DATA')

#Set interpolation method ("nearest"/"cubic"/"linear")
method='linear' 

#Set DEM extent         
cr1 = [445000, 452000, 8754000, 8760000]            

#Set destination for file outputs
target4 = destination + 'imgfiles/'
if not os.path.exists(target4):
    os.makedirs(target4)

cameraMatrix=cameraenvironment.getCamMatrixCV2()
distortP=cameraenvironment.getDistortCoeffsCV2() 
dem=cameraenvironment.getDEM()
imgset=velo._imageSet

#Cycle through data from image pairs   
for i in range(len(imn)-1):

    #Get image name and print
    print('\nVisualising data for ' + str(imn[i]))

    #Plot uv velocity points on image plane   
    print('Plotting image plane output')
    plotVeloPX(uvvel[i], uv0[i], uv1corr[i], 
               imgset[i].getImageCorr(cameraMatrix, distortP), 
               show=True, save=target4+'uv_'+imn[i])


    #Plot xyz velocity points on dem  
    print('Plotting XYZ output')
    plotVeloXYZ(xyzvel[i], xyz0[i], xyz1[i], 
                dem, show=True, save=target4+'xyz_'+imn[i])
    
                
    #Plot interpolation map
    print('Plotting interpolation map')
    grid, pointsextent = interpolateHelper(xyzvel[i], xyz0[i], xyz1[i], method)
    plotInterpolate(grid, pointsextent, dem, show=True, 
                    save=target4+'interp_'+imn[i])