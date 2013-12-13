backup
======

Backup files as binary strings to a specified directory (ideally network drive) using pickle.

Purpose:
  Not intended as version control or timemachine, but as an extra means to backup code.
  Backup.py searches user-secified directories for specifed file extensions, and stores
  those files as binary strings in pickled file, in a specified location, ideally to a 
  network drive.
