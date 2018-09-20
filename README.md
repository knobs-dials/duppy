duppy
================

Duplicate file detection by incrementally checking blocks of content, and only within file sets with the same size.

If you have a lot of largeish mostly-unique files, we avoid reading most data. ...though still seek a bunch,
which is why on smaller files we don't save much, particularly on platter derives as that becomes seek-bound.

Motivated by the observation that duplicate detection is largely IO-bound, and that unique files are usually unique in the first few dozen KB.



Options
===
```
Usage: duppy [options]

Options:
  -h, --help            show this help message and exit
  -v VERBOSE            0 prints only summary, 1 (default) prints file sets
  -R                    Default is recursive. Specify this (and files, e.g. *)
                        to not recurse into directories.
  -s MINSIZE            Minimum file size to include - because for small files we are seek-bound.
                        Defaults to 1. Note that all bytesize arguments understand values like '10M'
  -S MAXSIZE            Maximum file size to include. With -s allows working on ranges of sizes.
  -a STOPSIZE           Assume a set is identical after this amount of data.
                        Useful to avoid checking all of very large files, but
                        be careful when cobmbining with -d
  -b READSIZE           Inital read size, rounded to nearest KB. Defaults to
                        32KB.
  -m MAXREADSIZE        Chunks to read at a time once more checks out. Rounded
                        to nearest KB. defaults to 256KB. Can be higer on
                        RAID.
  -d, --delete          Apply rules to figure out what to delete. If a set is
                        decided, and you did not specify -n, will actually
                        delete.
  -n, --dry-run         When combined with -d, will only say what it would do.
  --elect-one-random    Mark one KEEP, the rest DELEte. Easiest and most
                        arbitrary.
  --keep-path=KEEP_SUBSTR
                        mark KEEP by absolute filename substring
  --delete-path=DELE_SUBSTR
                        mark DELEte by absolute filename substring
```



Example output:
```
    NOTE: Assuming files are identical after 32MB

    Creating list of files to check...
       no file arguments given, using current directory
    Done scanning, found 8423 files to check.

    Looking for duplicates...
    Assuming 2 files ('/dosgames/Full Throttle/image.img', '/dosgames/Full Throttle.img') are identical after 32MB (of 614MB)
    Done.
    
    Looking for duplicates...
     Done.
    
    [bunch of stuff omitted for brevity]
    
    1.8MB each:
    '/dosgames/temp_selection/KEEPER/CDCONT/KEEPER/KEEPER.EXE'
    '/dosgames/temp_selection/KEEPER/KEEPER.EXE'
    
    29MB each:
    '/dosgames/Quake2/lamber/pak0.PAK'
    '/dosgames/Quake2/lamber2/pak0.PAK'
    
    614MB each:
    '/dosgames/Full Throttle.img'
    '/dosgames/Full Throttle/image.img'
    
    Summary:
      Found 567 sets of duplicate files   (Warning: 1 were ASSUMED to be equal after 32MB)
        684 files could be removed,
        to save 2.4GB
      Spent 93 seconds    reading 3.0GB  (2.7% of 111GB)
```



Examples:

* Just list what is duplicate:

        duppy .

* fast and rough estimate of possible savings: ignore files smaller than 500KB (they would be most IO and probably little savings), assume files are identical after 32MB (when there are _large_ duplicates, they'll clobber your cache. Less reading is fine when you only want an estimation)

        duppy -s 500K -a 32M /dosgames

* work on the the specific files we mention, and no recursion if that includes a directory

        duppy -R frames_*

* When you have many files, e.g. checking all files between 1M and 2M, then 2 and 3, etc. is likelier to fit in page cache, and not clobber it so fast (also so that repeated runs are served from RAM)

        duppy -s 15M -S 20M /data/varied

* If you find duplicates, and any of them is in a directory called justdownloaded, choose that to delete

        duppy . -d -n --delete-path=/justdownloaded/




Notes / warnings:
=====
* safe around hardlinks in that it avoids adding the same inode twice. There is no space to be saved, and you're probably hardlinking for a reason. (We could still report them, though)

* Skips symlinks - does not consider them to be files, so won't delete the links or consider their content.
* ..but: it can still _break_ symlinks (and ensuring we won't would require scanning all mounted filesystems)

* On delete logic:
** think about what your delete rules mean. It'll refuse to delete every copy, but you can still make a mess for yourself.
** Standard disclaimer: While I have done basic sanity tests, but don't use any of the delete stuff on files you haven't backed up.



TODO:
=====
* test on windows

* rethink the delete rules. There's much more logic beneath all this, but it should be more obvious to use before I put it back in
* maybe rip out the rules after all? (I usually look at the output and delete manually)

* cleanup

* More sanity checks, and regression tests. I _really_ don't want to have to explain that we deleted all your files due to a silly bug  :)

* figure out why the 'total read' sum is incorrect


CONSIDERING:
* homedir config of permanent rules (for things like "always keep stuff from this dir")

* IO thread (minor speed gains?)

* progress bar to give feedback when checking larger files

* page-cache-non-clobbering (posix_fadvise(POSIX_FADV_DONTNEED), though it's only in os since py3.3)

* storing a cache with (fullpath,mtime,size,hash(first64kB)) or so in your homedir,
  for incremental checks will much less IO, particularly on slowly growing directories
  (storage should be on the order of ~35MB per 100k files, acceptable for most)

* hardlink duplicate files that are on the same filesystem

* rethink the delete and rule logic.

* --generate-ruleset   interactively generate a rule file based on common patterns in a set of files
