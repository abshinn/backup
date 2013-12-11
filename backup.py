#!/usr/bin/env python3

# TODO
#  - grab file contents in update only if file has changed
#  - create methods for file access/information
#  - create methods for file writing/copying

import os, sys, pickle, time, difflib
#import pdb DEBUG

class Backup(object):
    """Backup text files as binary strings.

    KEYWORD ARGUMENTS
       directories -- directories to search
                      (default: [cwd])
         backupdir -- directory to save pickled backup file
                      (defualt: cwd)
              exts -- determines which files to save based on their extension
                      (default: ["py", "txt", "R", "tex"])

    MAIN METHODS
          new -- create new pickled backup file
       update -- update pickled backup file

    USAGE
       For example, if you wanted to backup files in "notes" and "cv" directories to
       a "Dropbox" directory:
           >>> Backup(directories = ['~/notes', '~/cv'], backupdir = "~/Dropbox").new()
       And to update:
           >>> Backup(backupdir = "~/Dropbox").update()
    """

    class State:
        """Store the state of a backup in a simple object."""
        def __init__(self, info, dirs, files):
            self.info = info
            self.dirs = dirs
            self.files = files

    class Comparison:
        """Store backup changes in a simple object."""
        def __init__(self, new, changed, removed):
            self.new = new
            self.changed = changed
            self.removed = removed

    class stateCompare:
        """Store backup comparison objects in a simple object."""
        def __init__(self, dirComparison, filComparison):
            self.dirs = dirComparison
            self.files = filComparison

    def __init__(self, directories = [], backupdir = "", exts = ["py", "txt", "R", "tex"]):

        self.directories = directories
        self.exts = exts

        # define backup directory as current working directory if not specified
        if backupdir:
            self.backupdir = os.path.abspath(os.path.expanduser(backupdir))
        else:
            self.backupdir = os.getcwd()

        # name backup directory after computer name: nodename_backup.pkle
        self.backupfile = os.path.join(self.backupdir,os.uname().nodename + "_backup.pkle")


    def new(self):
        """ """
        self.pickleIt(self.current())

    def update(self):
        """ """
        if not os.path.isfile(self.backupfile): 
            print("Backup file does not exist in {self.backupdir}".format(self = self))
            return

        current = self.current()

        backup = self.load() 

        different = self.compare(current, backup)

        # note: the curr dictionaries have only one element in "modtime" and "contents" lists,
        #       and that element is the most recent information - so using the extend method
        #       will keep the newest modification at element 0
        for dirname in different.dirs.changed:
            current.dirs[dirname]["modtime"].extend(backup.dirs[dirname]["modtime"])
            # housekeeping: cleanup backup.dat by only keeping at most ten modifications
            if len(current.dirs[dirname]["modtime"]) > 10:
                current.dirs[dirname]["modtime"] = current.dirs[dirname]["modtime"][0:10]
        for filename in different.files.changed:
            current.files[filename]["modtime"].extend(backup.files[filename]["modtime"])
            current.files[filename]["contents"].extend(backup.files[filename]["contents"])
            # housekeeping: cleanup backup.dat by only keeping at most ten modifications
            if len(current.files[filename]["modtime"]) > 10: 
                current.files[filename]["modtime"] = current.files[filename]["modtime"][0:10]
                current.files[filename]["contents"] = current.files[filename]["contents"][0:10]

        self.pickleIt(current)

        btime_utc = time.strftime("%a %b %d %H:%M", time.gmtime())

        print('backup: {}; {}'.format(btime_utc, self.backupfile)) 
        print('  {self.new} new dir(s)\n  {self.removed} removed dir(s)'.format(self = different.dirs))
        print('  {} new file(s)\n  {} updated file(s)\n  {} removed file(s)'.format(len(different.files.new), 
            len(different.files.changed), len(different.files.removed))) 

        for dirname in different.dirs.removed:
            print("- {}".format(dirname))
        for dirname in different.dirs.new:
            print("+ {}".format(dirname))

        for filename in different.files.removed:
            print("- {}".format(filename))
        for filename in different.files.new:
            print("+ {}".format(filename))
        for filename in different.files.changed:
            print("u {}".format(filename))

    def current(self):
        """ """
        # initialize dictionaries
        alldirs = {}
        allfiles = {}
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
                        allfiles[absfilepath] = { 'modtime': [os.path.getmtime(absfilepath)],
                                                     'size': [os.path.getsize( absfilepath)],
                                                 'contents': [contents] }
        info = self.infodict(alldirs, allfiles)
        return self.State(info, alldirs, allfiles)

    def pickleIt(self, state):
        """Pickle a State object."""
        # pickle dictionaries - note the order for unpickling
        with open(self.backupfile, "wb") as pkle:
            pickle.dump(state.info,  pkle)
            pickle.dump(state.dirs,  pkle)
            pickle.dump(state.files, pkle)

        btime_utc = time.strftime("%a %b %d %H:%M", time.gmtime( state.info['btime_sys'] ))
        print('backup: {}; {} files saved to {}'.format(btime_utc, state.info['nfiles'], self.backupfile)) 

    def infodict(self, dirs, files):
        """Turn higher level backup information into a dictionary."""
        info = { 'nodename': os.uname().nodename,
                'btime_sys': time.time(),
                    'ndirs': len(dirs),
                   'nfiles': len(files),
              'directories': self.directories, # directories searched
                'backupdir': self.backupdir }
        return info

    def compare(self, state1, state2):
        """Compare two state objects, return stateCompare object."""

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

        dirComparison = self.Comparison(new_dirs, changed_dirs, removed_dirs)

        # store new and changed file names in aptly named dictionaries
        new_files, changed_files, ignore_files = {}, {}, {}
        for filename in state1.files:
            if filename not in state2.files: 
                new_files[filename] = state1.files[filename]
                print("new: {}".format(filename))
            elif state1.files[filename]['modtime'][0] > state2.files[filename]['modtime'][0]:
                changed_files[filename] = state1.files[filename]
                print("changed: {}".format(filename))
            elif state1.files[filename]['modtime'][0] < state2.files[filename]['modtime'][0]:
                ignore_files[filename] = state1.files[filename]
                print("WARNING") #TEMP create an error to raise here

        # check for removed files
        removed_files = {}
        for filename in state2.files:
            if filename not in state1.files:
                removed_files[filename] = state2.files[filename]
                print("removed: {}".format(filename))

        filComparison = self.Comparison(new_files, changed_files, removed_files)

        return self.stateCompare(dirComparison, filComparison)

    def load(self):
        """ """
        # open backup file
        with open(self.backupfile, "rb") as pkle:
            info = pickle.load(pkle)
            dirs = pickle.load(pkle)
            files = pickle.load(pkle)
        return self.State(info, dirs, files)

    def diff(binfile1, binfile2):
        """Returns True if two binary strings are different, False if no change has been made."""
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


if __name__ == "__main__":
    if "new" in sys.argv: 
        Backup(directories = ['~/notes', '~/R', '~/cv'], backupdir = "~/Dropbox").new()
    else:
        Backup(backupdir = "~/Dropbox").update()
