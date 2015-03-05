#!/usr/bin/python
import json
import os
#import re
import urllib2
import zipfile
import fnmatch
from urllib2 import urlopen, URLError, HTTPError


# @see http://stackoverflow.com/a/12886818
def unzip(source_filename, dest_dir):
    with zipfile.ZipFile(source_filename) as zf:
        for member in zf.infolist():
            # Path traversal defense copied from
            # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
            words = member.filename.split('/')
            path = dest_dir
            for word in words[:-1]:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir, ''): continue
                path = os.path.join(path, word)
            zf.extract(member, path)

# @see http://stackoverflow.com/q/4028697
def dlfile(url, filename = ''):
    # Open the url
    try:
        f = urlopen(url)

        if filename == '':
            filename = os.path.basename(url)

        with open(filename, "wb") as local_file:
            local_file.write(f.read())

    except HTTPError, e:
        print "HTTP Error:", e.code, url
    except URLError, e:
        print "URL Error:", e.reason, url

# @see http://stackoverflow.com/a/2186565
def findFiles(path):
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*.wav'):
            matches.append(os.path.join(root, filename))
    return matches

def printStatus(s):
    hr = '#' * 80 + '\n'
    print '%s%s\n%s' % (hr, s, hr)

def printStep(s):
    print '>>> %s' % s

def printMenu(sets):
    i = 0
    for s in sets:
        print '[%d] %s' % (i, s['name'])
        i += 1

    printStatus('Select sample set [0..%d]' % (len(sets)-1))

def loadConfig(path):
    return json.loads(open(path).read())

def getPath(targetFolder, key, currentVolume, currentFolder):
    path = "%s/%s-%d/%d" % (targetFolder, key, currentVolume, currentFolder)
    if not os.path.isdir(path):
        os.system("mkdir -p %s" % path)
    return path

def main():
    config = loadConfig('config.json')
    rootFolder = config['rootFolder']
    maxFilesPerVolume = config['maxFilesPerVolume']
    maxFolders = config['maxFolders']
    maxFilesPerFolder = config['maxFilesPerFolder']
    overwriteConvertedFiles = config['overwriteConvertedFiles']
    mode = config['mode']

    sets = json.loads(open('data.json').read())['sets']

    printMenu(sets)

    n = raw_input()
    try:
        n = int(n)
    except ValueError:
        printStatus('Invalid selection "%s"' % n)
        return

    if not sets[n]:
        printStatus('Invalid set "%d"' % n)
        return

    s = sets[n]
    url = s['url']
    name = s['name']
    key = s['key']
    sourceFolder = rootFolder + key + "/source"
    targetFolder = rootFolder + key + "/target"
    archive = "%s/%s.zip" % (sourceFolder, key)

    if not os.path.isdir(sourceFolder):
        printStep('Creating source dir %s' % sourceFolder)
        os.system("mkdir -p %s" % sourceFolder)

    if not os.path.isfile(archive):
        printStep('Downloading "%s" from %s into "%s"' % (name, url, archive))
        dlfile(url, archive)
    else:
        printStep('Skipping download, "%s" already exists' % archive)

    if not os.path.isdir(targetFolder):
        printStep('Creating target dir %s' % targetFolder)
        os.system("mkdir -p %s" % targetFolder)
    else:
        printStep('Skipping creating target dir, "%s" already exists' % targetFolder)


    printStep('Unzipping "%s"' % archive)
    unzip(archive, sourceFolder)

    files = findFiles(sourceFolder)

    filesInSet = len(files)
    currentVolume = 0
    currentFolder = 0
    currentFile = 0
    numFiles = 0
    path = getPath(targetFolder, key, currentVolume, currentFolder)

    printStep('Set contains %d files' % filesInSet)
    printStep('Mode: %s' % mode)

    if mode == 'spreadAcrossVolumes':
        numVolumes = (filesInSet // maxFilesPerVolume) + 1
        maxFilesPerFolder = (filesInSet // (numVolumes * maxFolders)) + 1
        maxFilesPerVolume = maxFilesPerFolder * maxFolders
    elif mode == 'spreadAcrossBanks':
        maxFilesPerFolder = min(maxFilesPerFolder, min(maxFilesPerVolume, filesInSet) // maxFolders)
    elif mode == 'voltOctish':
        maxFilesPerFolder = 60
    else:
        maxFilesPerFolder = 75

    numVolumes = (filesInSet // maxFilesPerVolume) + 1
    printStep('Spreading %d files across %d folders, %d files each (using %d volumes)' % (filesInSet, maxFolders, maxFilesPerFolder, numVolumes))

    for f in files:
        if currentFile < maxFilesPerFolder:
            baseName = os.path.basename(f)
            targetFile = "%s/%d.raw" % (path, currentFile)
            # convert to targetFolder
            cmd = "ffmpeg -i '%s' %s -f s16le -ac 1 -loglevel error -stats -ar 44100 -acodec pcm_s16le '%s'" % (
                f,
                '-y' if overwriteConvertedFiles else '',
                targetFile
            )
            dry = False
            if not dry:
                os.system(cmd)
            else:
                printStep(targetFile)

            currentFile += 1
            numFiles += 1

            if numFiles == maxFilesPerVolume:
                # next volume
                currentVolume += 1
                currentFolder = 0
                currentFile = 0

                path = getPath(targetFolder, key, currentVolume, currentFolder)

        else:
            currentFile = 0
            currentFolder += 1

            if currentFolder == maxFolders:
                # next volume
                currentVolume += 1
                currentFolder = 0
                currentFile = 0

            path = getPath(targetFolder, key, currentVolume, currentFolder)


    printStatus('Created %d volumes here: %s' % (currentVolume + 1, targetFolder))
    #for i in range(0, currentVolume + 1):
    #    os.system('du -hcs %s/%s-%d' % (targetFolder, key, i))

    os.system('open %s' % targetFolder)

if __name__ == '__main__':
    main()
