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
        else:

            if not os.path.isfile(self.backupfile): 
                print('Backup file does not exits in {self.backupdir}'.format(self=self))
                return

            # open backup file
            with open(self.backupfile, "rb") as f:
                self.back_info = pickle.load(f)
                self.back_dirs = pickle.load(f)
                self.back_files = pickle.load(f)
                #self.modification = pickle.load(f)
                #backupinfo = pickle.load(f)
                #self.backupinfo = BackupInfo(backupinfo)
            #print(self.backupinfo)

            self.directories = self.back_info['directories']
            self.exts = exts 

            self.backit()

            # store new and changed directories in aptly named dictionaries
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
                    print("WARNING") # create an error to raise here
            self.new_dirs = new_dirs
            self.changed_dirs = changed_dirs

            # check for removed directories
            removed_dirs = {}
            for dirname in self.back_dirs:
                if dirname not in self.curr_dirs:
                    removed_dirs[dirname] = self.back_dirs[dirname]
                    print("removed: {}".format(dirname))
            self.removed_dirs = removed_dirs

            # store new and changed files in aptly named dictionaries
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
                    print("WARNING") # create an error to raise here
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

            pdb.set_trace()

            if os.uname().nodename == self.curr_info['nodename']:
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
                # check to make sure current system's modification isn't newer than the backup system's mods
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
            if not os.path.isdir(directory): continue
            directory = os.path.abspath(os.path.expanduser(directory))
            print('b given directory: {}'.format(directory))
            # store root directory
            alldirs[directory] = { 'modtime': [os.path.getmtime(directory)] }
            for root, dirs, files in os.walk(directory):
                #if os.path.isfile(os.path.join(root,".backupignore")): continue
                for dirname in dirs:
                    absdirpath = os.path.join(root, dirname)
                    if not os.path.isdir(absdirpath): continue
                    print('b directory: {}'.format(absdirpath))
                    alldirs[absdirpath] = { 'modtime': [os.path.getmtime(absdirpath)] }
                for filename in files:
                    ext = os.path.splitext(filename)[-1].lstrip('.')
                    if ext in ['py', 'txt', 'R']:
                        absfilepath = os.path.join(root, filename)
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
        # include higher level backup information
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

        #self.abspath  = dictionary['abspath' ]
        #self.name     = dictionary['name'    ]
        #self.modtime  = dictionary['modtime ']
        #self.utcmtime = dictionary['utcmtime']
        #self.username = dictionary['username']
        #self.modhist  = dictionary['history' ]
        #self.size     = dictionary['size'    ]
        #self.contents = dictionary['contents']
# possibilities:
#   file changed
#   file didn't change
#   new file
#   file deleted
        #for filepath, filedict in self.diff.items():
        #    self.modification[filepath]
    def writeToFileSystem():
        pass
    def writeToBackup():
        pass
        #if self.pickled:
        #    backupinfo = {  "nodename": os.uname().nodename,
        #                   "btime_utc": time.ctime(), 
        #                   "btime_sys": time.time(),
        #                      "nfiles": len(modification),
        #                       "files": list(modification.keys()),
        #                      "moddir": moddir,
        #                 "directories": directories,
        #                        "exts": exts  }
        #    with open(os.path.join(self.moddir,"backup.dat")), "wb") as dat:
        #        pickle.dump(modification, dat)
        #        pickle.dump(backupinfo, dat)
        #else:
        #    return modification

def readmod(modfile):
    with open(modfile, "rb") as f:
        moddict = pickle.load(f)
    for absfilepath in moddict.keys():
        pass
    return moddict

if __name__ == "__main__":
    #Backup()
    Backup(directories = ['~/notes', '~/R'], backupdir = "~/Dropbox", newbackup = True)
