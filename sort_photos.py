import os
import sys
import shutil
import datetime
from datetime import *
import time

## I wrote this program to help me sort my photos while I'm
## traveling. Basically it assumes that I have output directories
## organized by date, like this:
## Pictures/2014/01/2014-01-01-Boston-Party
## Pictures/2014/02/2014-02-13-Milan
## Pictures/2014/02/2014-02-15-Rome

## I want to be able to input an SD card, or give a directory as an
## argument, and have the program sort the photos into the correct
## folders. However, there will also be old photos on the SD card, and
## it needs to transfer only the new ones. 

## I assume that I've transferred all photos up until a certain
## time. So if I walk through the list of photos on the SD card
## backwards, as soon as I've found a photo I've already transferred,
## I can assume all the rest are old photos that have already been
## transferred.

## From there, the program needs to figure out for each of the new
## photos if the right directory exists, and if not, prompt for where
## I was on a given day.

## There are some issues with time zones, namely when I forget to
## change the time zone on my camera. I'm not sure there's a solution
## to this, since my camera can't possibly know where I am, and as far
## as I know, does not store time zone information, only the timestamp
## itself.

## The other thing I want this program to do is keep track of
## backups. I like to leave the photos on the SD cards in case
## something happens to my laptop. However, I tend to take way too
## many photos, and on average I delete about half. No use to keep
## those around on an SD card with limited space. So the program also
## walks through all the old photos, and determines which old photos
## on my SD card no longer exist on the laptop, and deletes those.

## Speed consideration: The program _could_ go through the photos from
## earliest to latest, deleting old photos and prompting for new
## directories as needed. However, copying the photos can take a long
## time. I want to be able to run the program, enter any necessary
## information, and then walk away and let the program copy
## everything. So that's why it iterates through backwards first to
## figure out which new directories need to be created.


tformat = '%Y-%m-%d'
tformatlen = 10
toutformat = '%Y/%m/'

subdir = 'DCIM'

class Photo:
    def __init__(self, path, time):
        self.path = path
        self.time = time

    def get_date(self):
        return datetime.strftime(self.time, tformat)
    
    def get_filename(self):
        return os.path.split(self.path)[-1]

    ## Looks for day folders of form toutformat/tformat-$PLACE. For
    ## example, 2014/01/2014-01-10-Boston
    def getDayFolder(self, baseDir):
        tmpdir = baseDir
        # Ensure the subdirectories exist, and creates them if they
        # don't. This does not create superfluous photos since presumably
        # at least one photo is meant to be copied into the folder,
        # otherwise this function wouldn't be called.
        for tmp in toutformat.strip('/').split('/'):
            tmpdir = '/'.join([tmpdir, datetime.strftime(self.time, tmp)])
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
        return [datetime.strftime(self.time, toutformat) + x 
                for x in os.listdir(tmpdir)
                if x[:tformatlen] == datetime.strftime(self.time, tformat) 
                and os.path.isdir(baseDir + datetime.strftime(self.time, toutformat) + x)]


## Find camera. If the first argument does not exist, look for an SD
## card.

try:
    cameraDir = sys.argv[1] 
    cameraDirs = [cameraDir] # if a directory is given, assume it's flat
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


## Find output directory. If the second argument does not exist,
## output to the usual photos directory.

try:
    outDir = sys.argv[2]
except IndexError:
    outDir = '/Users/ylin/Pictures/Photos/'
    print 'Pictures will be output to', outDir


## Iterate through photos to determine total number and get full list

## This currently uses the last modified time, would be better if it
## used exif data.

photos = []
for cameraDir in cameraDirs:
    photosInDir = os.listdir(cameraDir)
    print 'Descending into folder %s, %s photos in folder' % (cameraDir, len(photosInDir))
    for photo in photosInDir:
        photopath = '/'.join([cameraDir, photo])
        phototime = datetime.utcfromtimestamp(os.path.getmtime(photopath)) \
            - timedelta(seconds = time.timezone)
        photoobj = Photo(photopath, phototime)
        photos.append(photoobj)
        
print '\n%s total photos on camera\n' % len(photos)


## Loop through sorted photo list to get missing folders and determine
## which need to be copied

## This assumes that going in reverse chronological order, all the
## photos are new until the first one that is not new, and all photos
## before that one have already been copied.

missingfolders = []
photostocopy = []
photostodelete = []
photos.sort(key = lambda x:x.time)
flag = False
for photo in photos[::-1]:
    photoFolder = photo.getDayFolder(outDir)

    if len(photoFolder) == 0: 
        photostocopy.append(photo)
        photodateobj = datetime.strptime(photo.get_date(), tformat)
        if photodateobj not in missingfolders:
            missingfolders.append(photodateobj)
    elif len(photoFolder) > 1: # it would be very strange if this actually happened
        print 'More than one folder found for %s. Please fix this problem and try again.' % photodate
        raise NameError('More than one folder for a given date')
    else:
        outPath = '/'.join([outDir, photoFolder[0], photo.get_filename()])
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
    os.mkdir(monthdir + '-'.join([datetime.strftime(folder, tformat), place]))


## Copy the new photos

photostocopy.sort()
for i, photo in enumerate(photostocopy):
    print photo.get_date()
    outpath = outDir + photo.getDayFolder(outDir)[0]
    print 'Copying', photo.path, '-->', outpath
    print '\tPhoto %s of %s, timestamp %s' % (i + 1, len(photostocopy), photo.time)
    shutil.copy2(photo.path, outpath)


## Delete the old photos from camera that are missing on computer

if deleteFlag:
    for photo in photostodelete:
        print 'Deleting photo: ', photo.path, photo.get_date(), photo.time
        os.remove(photo.path)

## Unmount the SD card

try:
    print '\n'
    os.system('diskutil unmount %s' % camera)
except NameError:
    pass

if photostocopy:
    print '\nDon\'t forget to synchronize Lightroom.\n'
