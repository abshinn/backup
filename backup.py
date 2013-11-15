#!/usr/bin/env python3

#
# Goal: to backup and keep track of chosen files and directories on the laptop and desktop
# - run backup to save current system's files
# - run backup to check for other system's changes

import os, pickle, time, difflib
import pdb

def diff(binfile1, binfile2):
    """diff - returns True if two strings are different, False if no change has been made"""
    # quick check: see if the length of the file has changed
    if len(binfile1) != len(binfile2):
        return True
    # deep check: check every character to make sure no changes have been made
    # note: methods quick_ratio or real_quick_ratio suffices for small text files
    else: 
        diff = difflib.SequenceMatcher(None, binfile1, binfile2).ratio()
        if diff == 1.0: 
            return False
        else:
            return True

class FileMod:
    def __init__(self, abspath):
        if os.path.isfile(abspath):
            self.abspath = abspath
            self.name = os.path.basename(self.abspath)
            self.modtime = os.path.getmtime(self.abspath)
            self.utcmtime = time.strftime("%a %b %d %H:%M", time.gmtime(self.modtime))
            self.size = os.path.getsize(self.abspath)
            self.username = os.uname().nodename
            self.modhist  = []
        else: print("{} not found".format(abspath))
    def getcontents(self):
        with open(self.abspath, "rb") as fileobj:
            self.contents = fileobj.read()
    def asdict(self):
        newdict = {}
        newdict['name'    ] = self.name
        newdict['modtime' ] = self.modtime 
        newdict['size'    ] = self.size 
        newdict['username'] = self.username
        newdict['modtime' ] = self.modtime
        newdict['utcmtime'] = self.utcmtime
        newdict['history' ] = self.modhist
        #dict['contents'] = self.contents
        return newdict
    def __str__(self):
        return "{self.size:>8}B [{self.utcmtime} on {self.username}] {self.abspath}".format(self=self)

class FileMod_fromdict(FileMod):
    def __init__(self, dictionary):
        self.abspath  = dictionary['abspath' ]
        self.name     = dictionary['name'    ]
        self.modtime  = dictionary['modtime ']
        self.utcmtime = dictionary['utcmtime']
        self.username = dictionary['username']
        self.modhist  = dictionary['history' ]
        self.size     = dictionary['size'    ]
        #self.contents = dictionary['contents']

class BackupInfo:
    def __init__(self, BackupInfoDict):
        self.nodename    = BackupInfoDict['nodename'   ]
        self.btime_utc   = BackupInfoDict['btime_utc'  ]
        self.btime_sys   = BackupInfoDict['btime_sys'  ]
        self.nfiles      = BackupInfoDict['nfiles'     ]
        self.files       = BackupInfoDict['files'      ]
        self.moddir      = BackupInfoDict['moddir'     ]
        self.directories = BackupInfoDict['directories']
        self.exts        = BackupInfoDict['exts'       ]
    def __str__(self):
        return "Last backup {self.btime_utc}; on {self.nodename}\n" \
               "  {self.nfiles} {self.exts!r} files from {self.directories!r}".format(self=self)

class State(object):
    def __init__(self, info, dirs, fils):
        self.info = info
        self.dirs = dirs
        self.fils = fils

class Comparison(object):
    def __init__(self, new, changed, removed):
        self.new = new
        self.changed = changed
        self.removed = removed
    def __format__(self, format_spec):
        if format_spec == 'l':
            return format(len(self), format_spec)

class stateCompare(object):
    def __init__(self, dirComparison, filComparison):
        self.dirs = dirComparison
        self.fils = filComparison


class Backup(object):
    def __init__(self, directories = [], backupdir = "", exts = ["py", "txt", "R", "tex"], newbackup = False):

        self.directories = directories
        self.exts = exts
        self.newbackup = newbackup

        # check for pickled backup file
        if not backupdir:
            backupdir = os.getcwd()

        self.backupdir = os.path.abspath(os.path.expanduser(backupdir))
        self.backupfile = os.path.join(self.backupdir,"backup.dat")

        self.current = self.getCurrent()

        if self.newbackup: 
            # nothing more to do
            return self.current

        if not os.path.isfile(self.backupfile): 
            print("Backup file does not exits in {self.backupdir}".format(self = self))
            return

        self.backup = self.loadBackup() 

        #TEMP override defualt
        self.directories = self.backup.info["directories"]

        # collect the current state of the system, using the same directories as in backup.dat
        self.current = self.getCurrent()

# read backup
# read current file system
# compare <---
# update

        #TEMP based on system and update time...
        # if backup is run on the same system of the previous backup:
        if os.uname().nodename == self.backup.info["nodename"]:

            self.different = self.compare(self.current, self.backup)

            self.update()

            self.writeToBackup()

            btime_utc = time.strftime("%a %b %d %H:%M", time.gmtime())
            #print('backup: {}; {}'.format(btime_utc, self.backupfile)) 
            #print('  {} new dir(s)\n  {} removed dir(s)'.format(len(self.different.dirs.new), 
            #    len(self.different.dirs.removed))) 
            #print('  {} new file(s)\n  {} updated file(s)\n  {} removed file(s)'.format(len(self.different.fils.new), 
            #    len(self.different.fils.changed), len(self.different.fils.removed))) 

            print('backup: {}; {}'.format(btime_utc, self.backupfile)) 
            print('  {self.new} new dir(s)\n  {self.removed} removed dir(s)'.format(self = self.different.dirs))
            print('  {} new file(s)\n  {} updated file(s)\n  {} removed file(s)'.format(len(self.different.fils.new), 
                len(self.different.fils.changed), len(self.different.fils.removed))) 

            for dirname in self.different.dirs.removed:
                print("- {}".format(filename))
            for dirname in self.different.dirs.new:
                print("+ {}".format(filename))

            for filename in self.different.fils.removed:
                print("- {}".format(filename))
            for filename in self.different.fils.new:
                print("+ {}".format(filename))
            for filename in self.different.fils.changed:
                print("u {}".format(filename))

        # if backup is run on a different system other than was used to update backup.py previously
        else: 
            print("b DIFFERENT NODENAME")
            #for directory in self.back_info['directories']:
            #    # if the current system has been updated since the backup on another system...
            #    if self.curr[directory]['modtime'] > self.back_info['btime_sys']:
            #        pass

#TEMP changes still need to be made
# if the current system has newer files than the backup file, update backup
# if the current system has older files than the backup file, update system
# ... and ignore directories controlled by git

            # check if directories on current system have been modified since backup.dat has been modified
            newer = []
            for dirname in self.directories:
                directory = os.path.abspath(os.path.expanduser(dirname))
                if os.path.isdir(directory):
                    if self.curr_dirs[directory]['modtime'][0] > self.back_info['btime_sys']:
                        newer.append(dirname)

            # ask
            if newer:
                print("WARNING: files on {} have been changed since the update on {}".format(os.uname().nodename, 
                    self.back_info['nodename']))
                if input("mock: merge changes between the two systems?") != "y": 
                    print("mock: exiting, no changes made")
                else: print("mock: merge changes")
            else:
                ask = input("mock: update current file system based on backup file\n press any key")

#TEMP ignore directories controlled by git, i.e., with .git directory
#TEMP ... but still make copies of the files
            # find new directories
            new_dirs = {}
            for dirname in self.back_dirs:
                if dirname not in self.curr_dirs: 
                    new_dirs[dirname] = self.back_dirs[dirname]
                    print("new: {}".format(dirname))
            self.new_dirs = new_dirs

            # check for removed directories
            removed_dirs = {}
            for dirname in self.curr_dirs:
                if dirname not in self.back_dirs:
                    removed_dirs[dirname] = self.back_dirs[dirname]
                    print("removed: {}".format(dirname))
            self.removed_dirs = removed_dirs

            # store new and changed file names in aptly named dictionaries
            new_files, changed_files, ignored_files = {}, {}, {}
            for filename in self.back_files:
                if filename not in self.curr_files: 
                    new_files[filename] = self.back_files[filename]
                    print("new: {}".format(filename))
                elif self.back_files[filename]['modtime'][0] > self.curr_files[filename]['modtime'][0]:
                    changed_files[filename] = self.back_files[filename]
                    print("changed: {}".format(filename))
                elif self.back_files[filename]['modtime'][0] < self.curr_files[filename]['modtime'][0]:
                    #if diff(self.back_files[filename]['contents'][0], self.curr_files[filename]['contents'][0]):
                    ignored_files[filename] = self.back_files[filename]
                    print("WARNING") #TEMP create an error to raise here
            self.new_files = new_files
            self.changed_files = changed_files
            self.ignored_files = ignored_files

            # check for removed files
            removed_files = {}
            for filename in self.curr_files:
                if filename not in self.back_files:
                    removed_files[filename] = self.curr_files[filename]
                    print("removed: {}".format(filename))
            self.removed_files = removed_files

            # print stats
            print("b {} last updated on {}:".format(self.backupfile, self.back_info['nodename']))
            print("b {} files created".format(len(self.new_files)))
            print("b {} files changed".format(len(self.changed_files)))
            print("b {} files removed".format(len(self.removed_files)))
            print("b {} files ignored".format(len(self.ignored_files)))
            print("b {} directories created".format(len(self.new_dirs)))
            print("b {} directories removed".format(len(self.removed_dirs)))

            # create and remove directories
            for dirname in self.new_dirs:
                print("mock: created directory: {}".format(dirname))
            for dirname in self.removed_dirs:
                print("mock: removed directory: {}".format(dirname))
            for filename in self.new_files:
                print("mock: created file: {}".format(filename))
            for filename in self.removed_files:
                print("mock: removed file: {}".format(filename))

            # update backup.dat
            print("mock: {} updated".format(self.backupfile))

    def getCurrent(self):
        """ """
        # initialize dictionaries
        alldirs = {}
        allfils = {}
        for directory in self.directories: 
            directory = os.path.abspath(os.path.expanduser(directory))
            if not os.path.isdir(directory): continue
            print('b given directory: {}'.format(directory))
            # store root directory
            alldirs[directory] = { 'modtime': [os.path.getmtime(directory)] }
            for root, dirs, files in os.walk(directory):
                for dirname in dirs:
                    absdirpath = os.path.join(root, dirname)
                    # don't include .git directory and subsequent directories
                    if '.git' in absdirpath.split(os.sep): continue
                    if not os.path.isdir(absdirpath): continue
                    print('b directory: {}'.format(absdirpath))
                    alldirs[absdirpath] = { 'modtime': [os.path.getmtime(absdirpath)] }
                for filename in files:
                    ext = os.path.splitext(filename)[-1].lstrip('.')
                    if ext in self.exts: 
                        absfilepath = os.path.join(root, filename)
                        # don't include files in .git directories
                        if '.git' in absfilepath.split(os.sep): continue
                        if not os.path.isfile(absfilepath): continue
                        print('b file: {}'.format(absfilepath))
                        with open(absfilepath, "rb") as fileobj:
                            contents = fileobj.read()
                        allfils[absfilepath] = { 'modtime': [os.path.getmtime(absfilepath)],
                                                    'size': [os.path.getsize( absfilepath)],
                                                'contents': [contents] }

        # pickle dictionaries - note the order for unpickling
        info = self.infodict(alldirs, allfils)
        if self.newbackup:
            with open(self.backupfile, "wb") as dat:
                pickle.dump(info, dat)
                pickle.dump(alldirs, dat)
                pickle.dump(allfils, dat)
            btime_utc = time.strftime("%a %b %d %H:%M", time.gmtime( info['btime_sys'] ))
            print('backup: {}; {} files saved to {}'.format(btime_utc, info['nfiles'], self.backupfile)) 
        else:
            return State(info, alldirs, allfils)

    def infodict(self, dirs, fils):
        """turn higher level backup information into a dictionary"""
        info = { 'nodename': os.uname().nodename,
                'btime_sys': time.time(),
                    'ndirs': len(dirs),
                   'nfiles': len(fils),
              'directories': self.directories, # directories searched
                'backupdir': self.backupdir }
        return info

    def compare(self, state1, state2):
        """compare state objects"""

        # store new and changed directory names in aptly named dictionaries
        new_dirs, changed_dirs = {}, {}
        for dirname in state1.dirs:
            if dirname not in state2.dirs: 
                new_dirs[dirname] = state1.dirs[dirname]
                print("new: {}".format(dirname))
            # note: directories get their modtime from the most recent file changed from within the directory
            elif state1.dirs[dirname]['modtime'][0] > state2.dirs[dirname]['modtime'][0]:
                changed_dirs[dirname] = state1.dirs[dirname]
                print("changed: {}".format(dirname))
            elif state1.dirs[dirname]['modtime'][0] < state2.dirs[dirname]['modtime'][0]:
                print("WARNING") #TEMP create an error to raise here

        # check for removed directories
        removed_dirs = {}
        for dirname in state2.dirs:
            if dirname not in state1.dirs:
                removed_dirs[dirname] = state2.dirs[dirname]
                print("removed: {}".format(dirname))

        dirComparison = Comparison(new_dirs, changed_dirs, removed_dirs)

        # store new and changed file names in aptly named dictionaries
        new_files, changed_files, ignore_files = {}, {}, {}
        for filename in state1.fils:
            if filename not in state2.fils: 
                new_files[filename] = state1.fils[filename]
                print("new: {}".format(filename))
            elif state1.fils[filename]['modtime'][0] > state2.fils[filename]['modtime'][0]:
                changed_files[filename] = state1.fils[filename]
                print("changed: {}".format(filename))
            elif state1.fils[filename]['modtime'][0] < state2.fils[filename]['modtime'][0]:
                ignore_files[filename] = state1.fils[filename]
                print("WARNING") #TEMP create an error to raise here

        # check for removed files
        removed_files = {}
        for filename in state2.fils:
            if filename not in state1.fils:
                removed_files[filename] = state2.fils[filename]
                print("removed: {}".format(filename))

        filComparison = Comparison(new_files, changed_files, removed_files)

        return stateCompare(dirComparison, filComparison)

    def update(self):
        #TEMP
        """Update and pickle backup file using current file system dictionary."""

        # update backup.dat if files or directories have changed
        # note: the curr dictionaries have only one element in "modtime" and "contents" lists,
        #       and that element is the most recent information - so using the extend method
        #       will keep the newest modification at element 0
        for dirname in self.different.dirs.changed:
            self.current.dirs[dirname]["modtime"].extend(self.backup.dirs[dirname]["modtime"])
            # housekeeping: cleanup backup.dat by only keeping at most ten modifications
            if len(self.current.dirs[dirname]["modtime"]) > 10:
                self.current.dirs[dirname]["modtime"] = self.current.dirs[dirname]["modtime"][0:10]
        for filename in self.different.fils.changed:
            self.current.fils[filename]["modtime"].extend(self.backup.fils[filename]["modtime"])
            self.current.fils[filename]["contents"].extend(self.backup.fils[filename]["contents"])
            # housekeeping: cleanup backup.dat by only keeping at most ten modifications
            if len(self.current.fils[filename]["modtime"]) > 10: 
                self.current.fils[filename]["modtime"] = self.current.fils[filename]["modtime"][0:10]
                self.current.fils[filename]["contents"] = self.current.fils[filename]["contents"][0:10]

    def writeToFileSystem():
        pass

    def writeToBackup(self):
        """Pickle backup file using current file system dictionary."""

        with open(self.backupfile, "wb") as dat:
            pickle.dump(self.infodict(self.current.dirs, self.current.fils), dat)
            pickle.dump(self.current.dirs, dat)
            pickle.dump(self.current.fils, dat)

    def loadBackup(self):
        """ """
        # open backup file
        with open(self.backupfile, "rb") as f:
            info = pickle.load(f)
            dirs = pickle.load(f)
            fils = pickle.load(f)
        return State(info, dirs, fils)


def readmod(modfile):
        pass

if __name__ == "__main__":
    Backup(backupdir = "~/Dropbox")
    #Backup(directories = ['~/notes', '~/R', '~/cv'], backupdir = "~/Dropbox", newbackup = True)
