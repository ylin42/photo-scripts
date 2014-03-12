import os
import sys
import shutil
import datetime
from datetime import *
import time

tformat = '%Y-%m-%d'
tformatlen = 10

toutformat = '%Y/%m/'

subdir = 'DCIM'

def getDayFolder(baseDir, ptime):
    monthdir = baseDir + datetime.strftime(ptime, toutformat)
    if not os.path.exists(monthdir):
        os.mkdir(monthdir)
    return [datetime.strftime(ptime, toutformat) + x 
            for x in os.listdir(monthdir)
            if x[:tformatlen] == datetime.strftime(ptime, tformat) 
            and os.path.isdir(baseDir + datetime.strftime(ptime, toutformat) + x)]

# Find camera

try:
    cameraDir = sys.argv[1]
    cameraDirs = [cameraDir]
except IndexError:
    mediaDir = '/Volumes'
    media = [x for x in os.listdir(mediaDir)
             if os.path.exists('/'.join([mediaDir, x, subdir]))]
    if not media:
        raise NameError('No camera found')
    elif len(media) > 1:
        print 'Found more than one camera:', media
        print 'Please specify source.'
        raise NameError('Multiple cameras found')
    else:
        camera = '/'.join([mediaDir, media[0]])
        cameraDir = '/'.join([mediaDir, media[0], subdir])
        print 'Found camera', cameraDir
        cameraDirs = ['/'.join([cameraDir, x]) for x in os.listdir(cameraDir)
                      if x not in ['CANONMSC']]

# Find output directory

try:
    outDir = sys.argv[2]
except IndexError:
    outDir = '/Users/ylin/Pictures/'
    print 'Pictures will be output to', outDir

## Iterate through photos to determine total number and get full list

photos = []
for cameraDir in cameraDirs:
    photosInDir = os.listdir(cameraDir)
    print 'Descending into folder %s, %s photos in folder' % (cameraDir, len(photosInDir))
    for photo in photosInDir:
        photopath = '/'.join([cameraDir, photo])
        phototime = datetime.utcfromtimestamp(os.path.getmtime(photopath)) \
            - timedelta(seconds = time.timezone)
        photodate = datetime.strftime(phototime, tformat)
        photos.append([photo, phototime, photopath, photodate])
        
print '\n%s total photos on camera\n' % len(photos)

## Loop through sorted photo list to get missing folders and determine
## which need to be copied

missingfolders = []
photostocopy = []
photostodelete = []
photos.sort(key = lambda x:x[1])
flag = False
for photo in photos[::-1]:
    photofile, phototime, photopath, photodate = photo
    photoFolder = getDayFolder(outDir, phototime)

    if len(photoFolder) == 0:
        photostocopy.append(photo)
        photodateobj = datetime.strptime(photodate, tformat)
        if photodateobj not in missingfolders:
            missingfolders.append(photodateobj)
    elif len(photoFolder) > 1: # it would be very strange if this actually happened
        print 'More than one folder found for %s. Please fix this problem and try again.' % photodate
        raise NameError('More than one folder for a given date')
    else:
        outPath = '/'.join([outDir, photoFolder[0], photofile])
        if flag:
            if not os.path.exists(outPath):
                photostodelete.append(photo)
            else:
                continue
        else:
            if os.path.exists(outPath):
                print '%s new photos found' % len(photostocopy)
                flag = True
            else:
                photostocopy.append(photo)

deleteFlag = False
if photostodelete:
    print '\n'
    #for photo in photostodelete:
    #    print photo
    f = raw_input('Delete %s missing old photos? (y/N) ' % len(photostodelete))
    if f == 'y': deleteFlag = True
else:
    print 'No missing old photos.'


## Create the missing daily destination folders

missingfolders.sort()
if missingfolders: print '%s missing day folders' % len(missingfolders)
for folder in missingfolders:
    place = raw_input('Location on %s? ' % datetime.strftime(folder, tformat))
    place = place.replace(' ', '-')
    monthdir = outDir + datetime.strftime(folder, toutformat)
    os.mkdir(monthdir + '/' + '-'.join([datetime.strftime(folder, tformat), place]))

## Copy the new photos

photostocopy.sort()
for i, photo in enumerate(photostocopy):
    photofile, phototime, photopath, photodate = photo
    outpath = outDir + getDayFolder(outDir, phototime)[0]
    print 'Copying', photopath, '-->', outpath
    print '\tPhoto %s of %s, timestamp %s' % (i + 1, len(photostocopy), phototime)
    shutil.copy2(photopath, outpath)

## Delete the old photos from camera that are missing on computer

if deleteFlag:
    for photo in photostodelete:
        photofile, phototime, photopath, photodate = photo
        print 'Deleting photo: ', photo[-2], photo[-1], phototime
        os.remove(photopath)

try:
    print '\n'
    os.system('diskutil unmount %s' % camera)
except NameError:
    pass

if photostocopy:
    print '\nDon\'t forget to synchronize Lightroom.\n'
