# Format Radio

## Helping you get sound packs into your Radio Music

### What it is

This is a small command line tool written in Python that prepares sound packs for use with [Music Thing Modular's Radio Music](https://github.com/TomWhitwell/RadioMusic).

### What it does

* Downloads sound packs from a configurable ["repository"](data.json), currently stocked with a selection of [packs from Music Radar](http://www.musicradar.com/news/tech/free-music-samples-download-loops-hits-and-multis-217833/)
* Converts WAV files to RAW (according to [RadioMusic specs](https://github.com/TomWhitwell/RadioMusic/wiki/SD-Card%3A-Format-%26-File-Structure#setting-up-files-on-the-micro-sd-card))
* Renames files to ensure 8.3 names (no clever shortening, just sequential naming of the files)
* Creates compatible folder structure (16 folders with 75 files max, no more than 330 files in total)
* Splits sound packs with more files across multiple *volumes*, ie multiple SD cards.

### What it doesn't do

The Radio Music plays mono files and SD cards are cheap, so the actual size of the files is not considered at all, the tool only handles converting the files and spreading them across a useful and valid folder structure.

The tool doesn't have anything to do with the SD cards themselves, it merely creates files and folders for you to copy onto a card.

The tool doesn't currently delete the downloaded source files (ie the original sound packs).

## Usage

Run it from the command line:
`$ ./create.py`

The tool lists all configured sample packs with number of samples and the size of the archive (NB: This is the filesize of the WAVs, after conversion the resulting files will likely be half that).

Enter the number of the sample pack you want to create.

Once done, the tool will open the folder containing all the volumes created from the sample pack.

## Configuration
The file [config.json](config.json) configures a few things. More documentation to follow.

* **rootFolder** sets the path where files are created
* **maxFilesPerVolume** sets the maximum number of files the Radio Music module can handle (on a single SD card)
* **maxFolders** sets the maximum number of folders the Radio Music module can handle
* **maxFilesPerFolder** sets the maximum number of files per folder the Radio Music can handle
* **overwriteConvertedFiles** determines whether ffmpeg is instructed to overwrite existing (RAW) files when converting
* **mode** determines how files are spread across folders and multiple volumes (large sample packs with more than 330 files can span multiple cards)
	* **spreadAcrossBanks** spreads all the files from a sample pack evenly across the banks (330 at the most), this is mostly useful with less than 330 files.
	* **spreadAcrossVolumes** spreads all the files from a sample pack evenly across the number of volumes required - this should give you the best overall result for large banks.
	* **maxCapacity** uses 75 samples per folder and fills each volume to the brim (16 folders, 330 files max). This fills up everything as dense as possible, you might end up with an almost empty last volume though.
	* **voltOctish** uses 60 samples per folder - with CV between 0..+5V we might be able to select a sample per semitone. Untested, possibly even unfounded.


## Sample Pack Repository

The file [data.json](data.json) lists the sample packs. Basically, this is a list of URLs to ZIP files containing WAV files. More documentation to follow.

## Requirements & Installation

* Currently tested on OS X only
* [Python](https://www.python.org/downloads/release/python-279/)
* [ffmpeg](https://www.ffmpeg.org/download.html) (the conversion bit can probably be changed to use [SoX](sox.sourceforge.net) quite easily)
* [I simply followed this article to get up and running with Python and pip](http://www.dabapps.com/blog/introduction-to-pip-and-virtualenv-python/)
* More info to follow...

## Roadmap

* Test installation on a fresh machine
* Complete documentation
* Remove OS specific stuff like os.system('open') (I'm guessing here that this won't work on Win machines)
* Clean up command line output
* Add download progress info, check whether pywget is better suited than urllib2
* Flesh out menus, allow selection of local folder instead of a repo entry
* Generate [settings.txt](https://github.com/TomWhitwell/RadioMusic/wiki/Customise-your-module%3A-Editing-settings.txt) from one of several profiles to go with the sound pack - helpful for one-shot sound packs etc.
