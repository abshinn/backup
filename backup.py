# use Python 3
#
# Goal: to backup and keep track of chosen files and directories on the laptop and desktop
# - run backup to save current system's files
# - run backup to check for other system's changes




import os, pickle, time

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
        self.nodename =    BackupInfoDict["nodename"   ]
        self.btime_utc =   BackupInfoDict["btime_utc"  ]
        self.btime_sys =   BackupInfoDict["btime_sys"  ]
        self.nfiles =      BackupInfoDict["nfiles"     ]
        self.files =       BackupInfoDict["files"      ]
        self.moddir =      BackupInfoDict["moddir"     ]
        self.directories = BackupInfoDict["directories"]
        self.exts =        BackupInfoDict["exts"       ]
    def __str__(self):
        return "Last backup {self.btime_utc}; on {self.nodename}\n" \
               "  {self.nfiles} {self.exts!r} files from {self.directories!r}".format(self=self)





def showbackup(backupdir=''):
    if not backupdir: backupdir = os.getcwd()

    backupdir_files = os.listdir(backupdir)
    
    for file in backupdir_files:
        if 'backup.dat' in file.split('_'):
            with open(file, "rb") as f:
                backupinfo = pickle.load(f)
            print(backupinfo)
            #print("{nodename} {nfiles} {btime_utc}".format(**backupinfo))
            




def modcheck(directories = [], moddir = '', exts = ['py', 'txt', 'R']):
    """given list of absdirpaths, pickle File classes"""

    # get mod directory
    if not moddir:
        moddir = os.getcwd()
    modfile = os.path.join(moddir,"backup.dat")

    # get modification log from pickled backup file
    # if none found, ask to create new if not found
    if not os.path.isfile(modfile): 
        y_or_n = input("No backup file found. Create new within {}? [y/n]".format(moddir))
        if y_or_n == "y": 
            Backup(directories=directories, moddir=moddir, exts=exts, pickle=True).backup()
        return

    # load pickled backup file
    with open(modfile, "rb") as f:
        backupdict = pickle.load(f)
    
    # run backup to obtain current state of files
    currentdict = backup(directories=directories, moddir=moddir, exts=exts)
    
    diff = []
    for abspath, filedict in currentdict.items():
        try:
            prev_mtime = backupdict[abspath]['modtime']
        except KeyError:
            continue
        mtime = filedict['modtime']
        if mtime > prev_mtime:
            diff.append(FileMod_fromdict(filedict))
        else: continue
    if not diff:
        print("No modifications made.")
    else:
        print("Modified Files")
        for filemodobj in diff:
            print(filemodobj)

class Backup:
    def __init__(self, directories = [], moddir = '', exts = ['py', 'txt', 'R'], pickled = False):

        # check for pickled backup file
        if not moddir:
            moddir = os.getcwd()
        else:
            self.moddir = moddir
        self.modfile = os.path.join(moddir, "backup.dat")
        if not os.path.isfile(self.modfile): 
            print('Backup file does not exits in {self.moddir}'.format(self=self))
            return

        # open backup file
        with open(self.modfile, "rb") as f:
            self.modification = pickle.load(f)
            backupinfo = pickle.load(f)
            self.backupinfo = BackupInfo(backupinfo)
        print(self.backupinfo)

        self.directories = self.backupinfo.directories
        self.exts = self.backupinfo.exts

        # check current state
        self.check()
        if self.diff:
            print("Files changed:")
            for filepath in self.diff.keys(): print(filepath)
        else: print("No files changed")

        #if not directories:
        #    self.directories = [os.getcwd()]
        #else:
        #    self.directories = directories
        #self.exts = exts
        #self.pickled = pickled 
    def check(self):
        modification = {} 
        for directory in self.directories: 
            if not os.path.isdir(directory): continue
            print("directory: " + directory)
            for root, dirs, files in os.walk(directory):
                #if os.path.isfile(os.path.join(root,".backupignore")): continue
                for file in files:
                    ext = os.path.splitext(file)[-1].lstrip('.')
                    if ext in self.exts:
                        absfilepath = os.path.join(root, file)
                        mod = FileMod(absfilepath)
                        modification[absfilepath] = mod.asdict()
                        print(mod)
        self.current = modification
        diff = {}
        for file in self.current:
            if file not in self.modification: diff[file] = self.current[file]
            elif self.current[file]['modtime'] > self.modification[file]['modtime']:
                diff[file] = self.current[file]
        self.diff = diff
    def update(self):
# update backup file
        for filepath, filedict in self.diff.items():
            pass
    def writeToFileSystem:
        pass
    def writeToBackup:
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
    #backup(['~/notes', '~/R'], pickled = True)
    #modcheck(['~/notes', '~/R'])
    showbackup()


