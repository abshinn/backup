# use Python 3
#
# Goal: to backup and keep track of chosen files and directories on the laptop and desktop
# - run backup to save current system's files
# - run backup to check for other system's changes

import os, pickle, time
import pdb

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


class Backup:
    def __init__(self, directories = [], backupdir = '', exts = ['py', 'txt', 'R'], newbackup = False):

        self.directories = directories

        # check for pickled backup file
        if not backupdir:
            backupdir = os.getcwd()
        self.backupdir = os.path.abspath(os.path.expanduser(backupdir))
        self.backupfile = os.path.join(self.backupdir,'backup.dat')

        self.newbackup = newbackup
        if self.newbackup:
            self.backit()
            return

        if not os.path.isfile(self.backupfile): 
            print('Backup file does not exits in {self.backupdir}'.format(self=self))
            return

        # open backup file
        with open(self.backupfile, "rb") as f:
            self.back_info = pickle.load(f)
            self.back_dirs = pickle.load(f)
            self.back_files = pickle.load(f)

        self.directories = self.back_info['directories']
        self.exts = exts 

        # collect the current state of the system, using the same directories as in backup.dat
        self.backit()
        
        #TEMP based on system and update time...
        # if backup is run on the same system of the previous backup:
        if os.uname().nodename == self.back_info['nodename']:

            # store new and changed directory names in aptly named dictionaries
            new_dirs, changed_dirs = {}, {}
            for dirname in self.curr_dirs:
                if dirname not in self.back_dirs: 
                    new_dirs[dirname] = self.curr_dirs[dirname]
                    print("new: {}".format(dirname))
                # note: directories get their modtime from the most recent file changed from within the directory
                elif self.curr_dirs[dirname]['modtime'][0] > self.back_dirs[dirname]['modtime'][0]:
                    changed_dirs[dirname] = self.curr_dirs[dirname]
                    print("changed: {}".format(dirname))
                elif self.curr_dirs[dirname]['modtime'][0] < self.back_dirs[dirname]['modtime'][0]:
                    print("WARNING") #TEMP create an error to raise here
            self.new_dirs = new_dirs
            self.changed_dirs = changed_dirs

            # check for removed directories
            removed_dirs = {}
            for dirname in self.back_dirs:
                if dirname not in self.curr_dirs:
                    removed_dirs[dirname] = self.back_dirs[dirname]
                    print("removed: {}".format(dirname))
            self.removed_dirs = removed_dirs

            # store new and changed file names in aptly named dictionaries
            new_files, changed_files, ignore_files = {}, {}, {}
            for filename in self.curr_files:
                if filename not in self.back_files: 
                    new_files[filename] = self.curr_files[filename]
                    print("new: {}".format(filename))
                elif self.curr_files[filename]['modtime'][0] > self.back_files[filename]['modtime'][0]:
                    changed_files[filename] = self.curr_files[filename]
                    print("changed: {}".format(filename))
                elif self.curr_files[filename]['modtime'][0] < self.back_files[filename]['modtime'][0]:
                    ignore_files[filename] = self.curr_files[filename]
                    print("WARNING") #TEMP create an error to raise here
            self.new_files = new_files
            self.changed_files = changed_files
            self.ignore_files = ignore_files

            # check for removed files
            removed_files = {}
            for filename in self.back_files:
                if filename not in self.curr_files:
                    removed_files[filename] = self.back_files[filename]
                    print("removed: {}".format(filename))
            self.removed_files = removed_files

            # update backup.dat if files or directories have changed
            for dirname in self.changed_dirs:
                self.curr_dirs[dirname]['modtime'].extend(self.back_dirs[dirname]['modtime'])
            for filename in self.changed_files:
                self.curr_files[filename]['modtime'].extend(self.back_files[filename]['modtime'])
                #self.cur_files[filename]['contents'].extend(self.back_files[filename]['contents'])
            # even if no files or directories have changed, still write to backup.dat
            with open(self.backupfile, "wb") as dat:
                pickle.dump(self.infodict(self.curr_dirs, self.curr_files), dat)
                pickle.dump(self.curr_dirs, dat)
                pickle.dump(self.curr_files, dat)
            print("b {} updated:".format(self.backupfile))
            print("b {} files created".format(len(self.new_files)))
            print("b {} files changed".format(len(self.changed_files)))
            print("b {} files removed".format(len(self.removed_files)))
            print("b {} directories created".format(len(self.new_dirs)))
            print("b {} directories changed".format(len(self.changed_dirs)))
            print("b {} directories removed".format(len(self.removed_dirs)))

        # if backup is run on a different system other than was used to update backup.py previously
        else: 
            for directory in self.back_info['directories']:
                # if the current system has been updated since the backup on another system...
                if self.curr[directory]['modtime'] > self.back_info['btime_sys']:
                    pass
#TEMP changes still need to be made
# if the current system has newer files than the backup file, update backup
# if the current system has older files than the backup file, update system
# ... and ignore directories controlled by git

            # store new and changed directory names in aptly named dictionaries 
            new_dirs, changed_dirs = {}, {}
            for dirname in self.back_dirs:
                if dirname not in self.curr_dirs: 
                    new_dirs[dirname] = self.back_dirs[dirname]
                    print("new: {}".format(dirname))
                # note: directories get their modtime from the most recent file changed from within the directory
                elif self.curr_dirs[dirname]['modtime'][0] > self.back_dirs[dirname]['modtime'][0]:
                    changed_dirs[dirname] = self.curr_dirs[dirname]
                    print("changed: {}".format(dirname))
                elif self.curr_dirs[dirname]['modtime'][0] < self.back_dirs[dirname]['modtime'][0]:
                    print("WARNING") #TEMP create an error to raise here
            self.new_dirs = new_dirs
            self.changed_dirs = changed_dirs

            ## check for removed directories
            #removed_dirs = {}
            #for dirname in self.back_dirs:
            #    if dirname not in self.curr_dirs:
            #        removed_dirs[dirname] = self.back_dirs[dirname]
            #        print("removed: {}".format(dirname))
            #self.removed_dirs = removed_dirs

            ## store new and changed file names in aptly named dictionaries
            #new_files, changed_files, ignore_files = {}, {}, {}
            #for filename in self.curr_files:
            #    if filename not in self.back_files: 
            #        new_files[filename] = self.curr_files[filename]
            #        print("new: {}".format(filename))
            #    elif self.curr_files[filename]['modtime'][0] > self.back_files[filename]['modtime'][0]:
            #        changed_files[filename] = self.curr_files[filename]
            #        print("changed: {}".format(filename))
            #    elif self.curr_files[filename]['modtime'][0] < self.back_files[filename]['modtime'][0]:
            #        ignore_files[filename] = self.curr_files[filename]
            #        print("WARNING") #TEMP create an error to raise here
            #self.new_files = new_files
            #self.changed_files = changed_files
            #self.ignore_files = ignore_files

            ## check for removed files
            #removed_files = {}
            #for filename in self.back_files:
            #    if filename not in self.curr_files:
            #        removed_files[filename] = self.back_files[filename]
            #        print("removed: {}".format(filename))
            #self.removed_files = removed_files

            ## update backup.dat if files or directories have changed
            #for dirname in self.changed_dirs:
            #    self.curr_dirs[dirname]['modtime'].extend(self.back_dirs[dirname]['modtime'])
            #for filename in self.changed_files:
            #    self.curr_files[filename]['modtime'].extend(self.back_files[filename]['modtime'])
            #    #self.cur_files[filename]['contents'].extend(self.back_files[filename]['contents'])
            ## even if no files or directories have changed, still write to backup.dat
            #with open(self.backupfile, "wb") as dat:
            #    pickle.dump(self.infodict(self.curr_dirs, self.curr_files), dat)
            #    pickle.dump(self.curr_dirs, dat)
            #    pickle.dump(self.curr_files, dat)



        pdb.set_trace()

        if os.uname().nodename == self.back_info['nodename']:
            print("b SAME NODENAME")
            # update backupfile if files or directories have chanaged
            #   need: to only allow a certain number of files to be kept
            for dirname in self.changed_dirs:
                self.curr_dirs[dirname]['modtime'].extend(self.back_dirs[dirname]['modtime'])
            for filename in self.changed_files:
                self.curr_files[filename]['modtime'].extend(self.back_files[filename]['modtime'])
                #self.cur_files[filename]['contents'].extend(self.back_files[filename]['contents'])
            with open(self.backupfile, "wb") as dat:
                pickle.dump(self.infodict(self.curr_dirs, self.curr_files), dat)
                pickle.dump(self.curr_dirs, dat)
                pickle.dump(self.curr_files, dat)
        else: # if the last backup was not on the current system:
            # if so, then write to file system
            print("b DIFFERENT NODENAME")
            # if running backup from a different system, a new directory will be present in the backup,
            # but not be present in the current system, therefore 'new' is 'removed' in this case
            self.new_dirs = self.removed_dirs
            self.new_files = self.removed_files
            # check to make sure current system's modification isn't newer than the backup system's mods
            print("{} files changed".format(len(self.changed_files)))
            print("{} new files".format(len(self.new_files)))
            print("{} directories changed".format(len(self.changed_dirs)))
            print("{} new directories".format(len(self.new_dirs)))
            if self.ignore_files:
                print("Files have been modified on this system since last backup! {}".format(len(self.ignore_files)))

        # if files are changed on same system, update backup file 
        # if files have been changed on other system:
        #     check to make sure updates are newer than current system's, then update file system using backup

    def backit(self):
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
                    if ext in ['py', 'txt', 'R']:
                        absfilepath = os.path.join(root, filename)
                        # don't include files in .git directories
                        if '.git' in absfilepath.split(os.sep): continue
                        if not os.path.isfile(absfilepath): continue
                        print('b file: {}'.format(absfilepath))
                        #with open(absfilepath, "rb") as fileobj:
                        #    contents = fileobj.read()
                        allfiles[absfilepath] = { 'modtime': [os.path.getmtime(absfilepath)],
                                                     'size': [os.path.getsize( absfilepath)] }
                                               # 'contents': contents }

        # pickle dictionaries - note the order for unpickling
        if self.newbackup:
            with open(self.backupfile, "wb") as dat:
                pickle.dump(self.infodict(alldirs, allfiles), dat)
                pickle.dump(alldirs, dat)
                pickle.dump(allfiles, dat)
        else:
            self.curr_info = self.infodict(alldirs, allfiles)
            self.curr_dirs = alldirs
            self.curr_files = allfiles

    def infodict(self, dirs, files):
        """turn higher level backup information into a dictionary"""
        info = { 'nodename': os.uname().nodename,
                'btime_sys': time.time(),
                    'ndirs': len(dirs),
                   'nfiles': len(files),
              'directories': self.directories, # directories searched
                'backupdir': self.backupdir }
        return info
    def update(self):
        """Update backup.dat"""
        # new file
        for filepath, filedict in self.new.items():
            self.modification[filepath] = filedict

        # updated file
        for filepath, filedict in self.changed.items():
            modtime = filedict['modtime']
            # turn dictionary items into lists containing previous updates
            modtime
            self.modification[filepath]['modtime'] = filedict['modtime']

    def writeToFileSystem():
        pass
    def writeToBackup():
        pass

def readmod(modfile):
    with open(modfile, "rb") as f:
        moddict = pickle.load(f)
    for absfilepath in moddict.keys():
        pass
    return moddict

if __name__ == "__main__":
    #Backup(backupdir = "~/Dropbox")
    #Backup(directories = ['~/notes', '~/R'], backupdir = "~/Dropbox", newbackup = True)
