#!/usr/bin/python
import json
import os
import sys
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
            p = os.path.join(root, filename)
            if (not '__MACOSX/' in p):
                matches.append(p)
    return matches

def hr():
    print '#' * 80

def printStatus(s):
    hr()
    print s
    hr()

def printStep(s):
    print '>>> %s' % s

def printSetMenu(sets):
    i = 0
    hr()
    for s in sets:
        print '[%d] %s' % (i, s['name'])
        i += 1

    printStatus('Select sample set [0..%d]' % (len(sets)-1))

def printProfileMenu(profiles):
    i = 0
    hr()
    for p in profiles:
        print '[%d] %s' % (i, p['_name'])
        i += 1

    printStatus('Select settings profile [0..%d]' % (len(profiles)-1))

def loadConfig(path):
    return json.loads(open(path).read())

def getPath(targetFolder, key, currentVolume, currentFolder):
    path = "%s/%s-%d/%d" % (targetFolder, key, currentVolume, currentFolder)
    if not os.path.isdir(path):
        os.system("mkdir -p %s" % path)
    return path

def getInput():
    n = raw_input()
    try:
        n = int(n)
    except ValueError:
        exit('Invalid selection "%s"' % n)
        #printStatus('Invalid selection "%s"' % n)
        return None
    return n

def getSettings(config):
    profiles = config['profiles']
    printProfileMenu(profiles)

    n = getInput()
    if not n in range(0, len(profiles)):
        exit('Invalid profile "%d"' % n)
        return

    # Yes, well...
    defaultProfile = profiles[0]
    for p in profiles:
        if p['_name'] == 'default':
            defaultProfile = p
            break

    # @see http://stackoverflow.com/a/26853961
    settings = defaultProfile.copy()
    settings.update(profiles[n])
    del settings['_name']
    return settings

def getSet(sets):
    printSetMenu(sets)
    n = getInput()
    if not n in range(0, len(sets)):
        exit('Invalid set "%d"' % n)
        return
    return sets[n]

def writeSettings(path, settings):
    with open(path + 'settings.txt', 'w') as f:
        for k, v in settings.iteritems():
            f.write('{}={}\n'.format(k, v))

def exit(s):
    sys.exit(s)

def main():
    config = loadConfig('config.json')

    settings = getSettings(config)

    rootFolder = config['rootFolder']
    maxFilesPerVolume = config['maxFilesPerVolume']
    maxFolders = config['maxFolders']
    maxFilesPerFolder = config['maxFilesPerFolder']
    overwriteConvertedFiles = config['overwriteConvertedFiles']
    mode = config['mode']

    # load set data
    sets = json.loads(open('data.json').read())['sets']
    # select a set
    s = getSet(sets)

    url = s['url']
    name = s['name']
    key = s['key']
    sourceFolder = rootFolder + key + "/source"
    targetFolder = rootFolder + key # + "/target"
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
    writeSettings("%s/%s-%d/" % (targetFolder, key, currentVolume), settings)

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
                writeSettings("%s/%s-%d/" % (targetFolder, key, currentVolume), settings)


        else:
            currentFile = 0
            currentFolder += 1

            if currentFolder == maxFolders:
                # next volume
                currentVolume += 1
                currentFolder = 0
                currentFile = 0

            path = getPath(targetFolder, key, currentVolume, currentFolder)
            writeSettings("%s/%s-%d/" % (targetFolder, key, currentVolume), settings)

    printStatus('Created %d volumes here: %s' % (currentVolume + 1, targetFolder))
    #for i in range(0, currentVolume + 1):
    #    os.system('du -hcs %s/%s-%d' % (targetFolder, key, i))

    # clean up
    #os.system('rm -rf %s' % sourceFolder)
    

if __name__ == '__main__':
    main()
