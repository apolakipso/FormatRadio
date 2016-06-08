#!/usr/bin/python
import json
import os
import sys
import urllib2
import zipfile
import fnmatch
from urllib2 import urlopen, URLError, HTTPError

EXT_RAW = '.RAW'
EXT_WAV = '.WAV'
SETTINGS_FILE = 'settings.txt'

# @see http://stackoverflow.com/a/12886818
def unzip(source_filename, dest_dir):
    # @note path traversal vulnerability in extractall has been fixed as of Python 2.7.4
    zipfile.ZipFile(source_filename).extractall(dest_dir)

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
def findFiles(path, extensions):
    matches = []
    for root, dirnames, filenames in os.walk(path, topdown = False):
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            if (ext.upper() in extensions):
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

def selectProfile(profiles):
    printProfileMenu(profiles)
    n = getInput()
    if not n in range(0, len(profiles)):
        exit('Invalid profile "%d"' % n)
        return
    return n

def getProfile(profiles, whichProfile = None):
    if (whichProfile == None):
        whichProfile = selectProfile(profiles)

    defaultProfile = profiles[0]
    for p in profiles:
        if p['_name'] == 'default':
            defaultProfile = p
            break

    # @see http://stackoverflow.com/a/26853961
    profile = defaultProfile.copy()
    profile.update(profiles[whichProfile])
    del profile['_name']
    return profile

def selectSet(sets):
    printSetMenu(sets)
    n = getInput()
    if not n in range(0, len(sets)):
        exit('Invalid set "%d"' % n)
        return
    return n

def getSet(sets, whichSet):
    if (whichSet == None):
        whichSet = selectSet(sets)
    return sets[whichSet]

def writeSettings(path, settings):
    with open(path, 'w') as f:
        for k, v in settings.iteritems():
            f.write('{}={}\n'.format(k, v))

def exit(s):
    sys.exit(s)

def convertFile(sourceFile, targetFile, overwrite):
    cmd = "ffmpeg -i '%s' %s -f s16le -ac 1 -loglevel error -stats -ar 44100 -acodec pcm_s16le '%s'" % (
        sourceFile,
        '-y' if overwrite else '',
        targetFile
    )
    print cmd
    os.system(cmd)

def setExtension(filename, extension):
    name, ext = os.path.splitext(filename)
    return name + extension

def main():
    config = loadConfig('config.json')
    profiles = config['profiles']

    settings = getProfile(profiles, int(sys.argv[1]) if len(sys.argv) > 1 else None)

    rootFolder = config['rootFolder']
    maxFilesPerVolume = config['maxFilesPerVolume']
    maxFolders = config['maxFolders']
    maxFilesPerFolder = config['maxFilesPerFolder']
    overwriteConvertedFiles = config['overwriteConvertedFiles']
    mode = config['mode']

    # load set data
    sets = json.loads(open('data.json').read())['sets']
    # select a set
    s = getSet(sets, int(sys.argv[2]) if len(sys.argv) > 2 else None)

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

    if 'mode' in s:
        mode = s['mode']

    printStep('Mode: %s' % mode)

    # Hacky interlude if we just need to copy and convert the files
    # while keeping the folder structure as is
    if mode == 'convertOnly':
        # check source
        sourcePath = sourceFolder + (s['path'] if 'path' in s else '')
        # if not sourcePath.endswith('/'): sourcePath += '/'
        if not os.path.isdir(sourcePath):
            exit("Source path is invalid: %s" % sourcePath)

        # create target
        targetFolder = "%s/%s/" % (targetFolder, key)
        os.system("mkdir -p %s" % targetFolder)

        # copy source files
        cmd = "cp -PR %s %s" % (sourcePath, targetFolder)
        os.system(cmd)

        if not os.path.isfile(targetFolder + SETTINGS_FILE):
            # write settings
            printStep('Writing settings: %s' % targetFolder + SETTINGS_FILE)
            writeSettings(targetFolder + SETTINGS_FILE, settings)
        else:
            printStep('Keeping settings contained in archive')

        files = findFiles(targetFolder, [EXT_WAV])

        if len(files) > 0:
            printStep('Converting WAV files')
            # convert raw files and delete copied sources
            for sourceFile in files:
                targetFile = setExtension(sourceFile, EXT_RAW)
                convertFile(sourceFile, targetFile, True)
                cmd = "rm '%s'" % sourceFile
                os.system(cmd)
        print
        printStep('Done.')
        return

    files = findFiles(sourceFolder, [EXT_RAW, EXT_WAV])
    filesInSet = len(files)
    currentVolume = 0
    currentFolder = 0
    currentFile = 0
    numFiles = 0

    printStep('Set contains %d files' % filesInSet)

    os.system("mkdir -p %s/%s-%d" % (targetFolder, key, currentVolume))

    writeSettings("%s/%s-%d/%s" % (targetFolder, key, currentVolume, SETTINGS_FILE), settings)
    path = getPath(targetFolder, key, currentVolume, currentFolder)

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
            name, ext = os.path.splitext(f)

            if (ext.upper() == EXT_WAV):
                # WAV file, convert
                convertFile(f, targetFile, overwriteConvertedFiles)
                # cmd = ["ffmpeg", "-i", pipes.quote(f), '-loglevel', 'quiet', '-y' if overwriteConvertedFiles else '', "-f", "s16le", "-ac", "1", "-ar", "44100", "-acodec", "pcm_s16le",  pipes.quote(targetFile)]
                # r = subprocess.call(cmd, shell=False)
                # if (r != 0):
                #     printStep("Error converting file %s" % f)
                #     break

            else:
                # RAW file, just copy
                cmd = "cp '%s' '%s'" % (f, targetFile)
                os.system(cmd)

            currentFile += 1
            numFiles += 1

            if numFiles == maxFilesPerVolume:
                # next volume
                currentVolume += 1
                currentFolder = 0
                currentFile = 0
                path = getPath(targetFolder, key, currentVolume, currentFolder)
                writeSettings("%s/%s-%d/%s" % (targetFolder, key, currentVolume, SETTINGS_FILE), settings)

        else:
            currentFile = 0
            currentFolder += 1

            if currentFolder == maxFolders:
                # next volume
                currentVolume += 1
                currentFolder = 0
                currentFile = 0

            path = getPath(targetFolder, key, currentVolume, currentFolder)
            writeSettings("%s/%s-%d/%s" % (targetFolder, key, currentVolume, SETTINGS_FILE), settings)

    printStatus('Created %d volumes here: %s' % (currentVolume + 1, targetFolder))
    #for i in range(0, currentVolume + 1):
    #    os.system('du -hcs %s/%s-%d' % (targetFolder, key, i))

    # clean up
    #os.system('rm -rf %s' % sourceFolder)

    if (os.name == 'mac'):
        os.system('open %s' % targetFolder)

if __name__ == '__main__':
    main()
