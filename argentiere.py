'''
PyTrx (c) is licensed under a MIT License.

You should have received a copy of the license along with this
work. If not, see <https://choosealicense.com/licenses/mit/>.


This script uses PyTrx, an object-oriented programme created for the 
purpose of calculating real-world measurements from oblique images and 
time-lapse image series.

The functions used here do not depend on class object inputs and can be run as 
stand-alone functions.

This script provides the user with a more detailed 
overview of PyTrx's functionality beyond its object-oriented structure. It also 
allows flexible intervention and adaptation where needed. 
'''

#Import packages
import cv2, glob, sys
import glob
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# #Import PyTrx modules
print('Importing from PyTrx')
from PyTrx.CamEnv import setProjection, optimiseCamera, computeResidualsXYZ
from PyTrx.DEM import load_DEM
from PyTrx import Velocity
from PyTrx import FileHandler
from PyTrx import Utilities 

 
#------------------------   Define inputs/outputs   ---------------------------

print('\nDEFINING DATA INPUTS')

#Camera name, location (XYZ) and pose (yaw, pitch, roll)
camname = 'CAM5'
camloc = np.array([1011242.816, 6545738.756, 2850.000])
campose = np.array([-56, 3, 5]) 

#Define image folder and image file type for velocity tracking
imgFiles = './images/*.JPG'

#Define calibration file path
calibPath = './camenv_data/calib/Calib_argentiere.txt'

#Load DEM from path       
DEMpath = './camenv_data/dem/DEM.tif'

#Define masks for velocity and homography point generation
vmaskPath_s = './camenv_data/masks/StableTerrain_mask_image.jpg'
vmaskPath_s2 = './camenv_data/masks/Cone_mask_image.jpg'
vmaskPath_d = './camenv_data/masks/Cone_mask_dem.jpg'
hmaskPath = './camenv_data/masks/Cone_mask_homography.jpg'

#Define reference image (where GCPs have been defined)
refimagePath = './camenv_data/refimages/23_07150870.JPG'

#Define GCPs (world coordinates and corresponding image coordinates)
GCPpath = './camenv_data/gcps/gcps.txt'

print('\nDEFINING DATA OUTPUTS')

#Shapefile output (with WGS84 projection)
target1 = './results/Argentiere_test_2024_06_27_sparse/' 
target2 = './results/Argentiere_test_2024_06_14_dense/'
projection = 2154


#--------------------------   Define parameters   -----------------------------

#DEM parameters 
DEMdensify = 1                      #DEM densification factor (for smoothing)

#Optimisation parameters
optparams = 'YPR'                   #Parameters to optimise
optmethod = 'trf'                   #Optimisation method

#Image enhancement paramaters
band = 'L'                          #Image band extraction (R, B, G, or L)
equal = True                        #Histogram equalisation?

#Sparse velocity parameters
vwin = (25,25)                      #Sparse corner matching window size
vback = 1.0                         #Back-tracking threshold  
vmax = 5000                         #Maximum number of corners to seed (50.000)
vqual = 0.1                         #Corner quality for seeding
vmindist = 10.0                      #Minimum distance between points (5.0)

#Dense velocity parameters
vgrid = [50,50]                     #Dense matching grid distance
vtemplate=10                        #Template size
vsearch=50                          #Search window size
vmethod='cv2.TM_CCORR_NORMED'       #Method for template matching
vthres=0.8                          #Threshold average template correlation

#General velocity parameters
vminfeat = 1                        #Minimum number of points to track
                         
#Homography parameters
hwin = (25,25)                      #Stable pt tracking window size
hmethod = cv2.RANSAC                #Homography calculation method 
                                    #(cv2.RANSAC, cv2.LEAST_MEDIAN, or 0)
hreproj = 5.0                       #Maximum allowed reprojection error
hback = 0.5                         #Back-tracking threshold
herr = True                         #Calculate tracking error?
hmax = 50000                        #Maximum number of points to seed
hqual = 0.1                         #Corner quality for seeding
hmindist = 5.0                      #Minimum distance between seeded points
hminfeat = 4                        #Minimum number of seeded points to track


#----------------------   Set up camera environment   -------------------------

print('\nLOADING DEM')
dem = load_DEM(DEMpath)
dem = dem.densify(DEMdensify)


print('\nLOADING GCPs')
GCPxyz, GCPuv = FileHandler.readGCPs(GCPpath)


print('\nLOADING CALIBRATION')
calib_out = FileHandler.readMatrixDistortion(calibPath)
matrix = np.transpose(calib_out[0])
tancorr = calib_out[1]
radcorr = calib_out[2]
focal = [matrix[0,0], matrix[1,1]]
camcen = [matrix[0,2], matrix[1,2]]


print('\nLOADING IMAGE FILES')
imagelist = sorted(glob.glob(imgFiles))
im1 = FileHandler.readImg(imagelist[0], band, equal)
imn1 = Path(imagelist[0]).name


print('\nOPTIMISING CAMERA ENVIRONMENT')
projvars = [camloc, campose, radcorr, tancorr, focal, camcen, refimagePath] 
new_projvars = optimiseCamera('YPR', projvars, GCPxyz, GCPuv, 
                              optmethod=optmethod, show=True)
new_projvars = optimiseCamera('INT', new_projvars, GCPxyz, GCPuv, 
                              optmethod=optmethod, show=True)


print('\nCOMPILING TRANSFORMATION PARAMETERS')
camloc1, campose1, radcorr1, tancorr1, focal1, camcen1, refimagePath = new_projvars

matrix1 = np.array([focal1[0], 0, camcen[0], 0, focal1[1], 
                   camcen[1], 0, 0, 1]).reshape(3,3)

distort = np.hstack([radcorr1[0], radcorr1[1],          
                     tancorr1[0], tancorr1[1],          
                     radcorr1[2]])
 
new_invprojvars = setProjection(dem, camloc1, campose1, 
                            radcorr1, tancorr1, focal1, 
                            camcen1, refimagePath)

campars = [dem, new_projvars, new_invprojvars]                 

residuals = computeResidualsXYZ(new_invprojvars, GCPxyz, GCPuv, dem)

print('\nLOADING MASKS')
print('Defining velocity mask')
vmask1 = FileHandler.readMask(im1, vmaskPath_s) # stable terrain mask on image
vmask2 = FileHandler.readMask(im1, vmaskPath_s2) # cone mask on image
vmask3 = Velocity.readDEMmask(dem, im1, new_invprojvars, vmaskPath_d) # cone mask on DEM

print('Defining homography mask')
hmask = FileHandler.readMask(None, hmaskPath)

plt.imshow(vmask1)
plt.show()

plt.imshow(vmask2)
plt.show()

plt.imshow(vmask3)
plt.show()

#--------------------   Plot camera environment info   ------------------------

print('\nPLOTTING CAMERA ENVIRONMENT INFO')

#Load reference image
refimg = FileHandler.readImg(refimagePath) 
imn = Path(refimagePath).name    

#Show Prinicpal Point in image
Utilities.plotPrincipalPoint(camcen1, refimg, imn)

#Show corrected and uncorrected image
Utilities.plotCalib(matrix1, distort, refimg, imn)

#Show GCPs
Utilities.plotGCPs([GCPxyz, GCPuv], refimg, imn, 
                   dem, camloc, extent=None)    


#----------------------   Calculate velocities   ------------------------------

print('\nCALCULATING VELOCITIES')

#Create empty output variables
velo1 = []                                    
homog = []

#Cycle through image pairs (numbered from 0)
for i in range(len(imagelist)-1):

    #Re-assign first image in image pair
    im0=im1
    imn0=imn1
                    
    #Get second image (corrected) in image pair
    im1 = FileHandler.readImg(imagelist[i+1], band, equal)
    imn1 = Path(imagelist[i+1]).name                                                       
    
    
    print('\nProcessing images: ' + str(imn0) + ' and ' + str(imn1))
        
    #Calculate homography between image pair
    print('Calculating homography...')

    hg = Velocity.calcSparseHomography(im0, im1, vmask1, [matrix1,distort], 
                                       hmethod, hreproj, hwin, hback, hminfeat, 
                                       [hmax, hqual, hmindist])
    homog.append(hg)
                             
    #Calculate velocities between image pair
    print('Calculating sparse velocities...')
    vl1 = Velocity.calcSparseVelocity(im0, im1, vmask2, [matrix1,distort], 
                                      [hg[0],hg[3]], new_invprojvars, vwin, 
                                      vback, vminfeat, [vmax,vqual,vmindist])  
 
    velo1.append(vl1)         

#---------------------------  Export data   -----------------------------------

print('\nWRITING DATA TO FILE')

#Get all image names
names=[]
for i in imagelist:
    names.append(str(Path(i).name).split('.JPG')[0])

#Extract xyz velocities, uv velocities, and xyz0 locations
xyzvel1=[item[0][0] for item in velo1] 
xyzerr1=[item[0][3] for item in velo1]
uvvel1=[item[1][0] for item in velo1]
xyz01=[item[0][1] for item in velo1]
xyz11=[item[0][2] for item in velo1]
uv0=[item[1][1] for item in velo1] 
uv1corr=[item[1][3] for item in velo1]

#Write points to shp file                
#FileHandler.writeVeloSHP(xyzvel1, xyzerr1, xyz01, names, target1, projection)  
    

#----------------------------- Plot data --------------------------------------
ref_img = im1 = FileHandler.readImg(imagelist[0], band, equal)

for i in range(len(imagelist)-1):
    Utilities.plotVeloPX(uvvel1[i], uv0[i], uv1corr[i], 
               ref_img, show=True, save=None)
    
    Utilities.plotVeloXYZ(xyzvel1[i], xyz01[i], xyz11[i], 
                dem, show=True, save=None)
    
    #Set interpolation method ("nearest"/"cubic"/"linear")
    method='linear' 
    grid, pointsextent = Utilities.interpolateHelper(xyzvel1[i], xyz01[i], xyz11[i], method)
    Utilities.plotInterpolate(grid, pointsextent, dem, show=True, 
                    save=None)      