duppy
================

Duplicate file detection by incrementally checking blocks of content.

Motivated by the observation that duplicate detection is largely IO-bound (and the larger the files, specifically read-bound), and that unique files are usually unique in the first few dozen KB. If you have a lot of large mostly-unique files, we avoid a lot of reading.


Options
===
```
Usage: duppy [options]

Options:
  -h, --help            show this help message and exit
  -v VERBOSE            0 prints only summary, 1 (default) prints file sets
  -s MINSIZE            Minimum file size to include. Defaults to 1.Note that
                        all bytesize arguments understand values like '10M'
  -S MAXSIZE            Maximum file size to include.
  -R                    Default is recursive. Specify this (and files, e.g. *)
                        to not recurse into directories.
  -a STOPLEN            Assume a set is identical after this amount of data.
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


Examples:

* Just list what is duplicate:

        duppy .

* work on the the specific files we mention, and no recursion if that includes a directory

        duppy -R data*

* If you find duplicates, and any of them is in a directory called justdownloaded, choose that to delete

        duppy . -d -n --delete-path=/justdownloaded/

* fast and rough estimate of possible space savingss: ignore files smaller than 500KB, assume files are identical after 32MB

        duppy -s 500K -a 32M /dosgames


The last because 
* small files mean relatively much IO for relatively little savings

* when there _are_ a lot of large duplicates, it will most of its time verifying them, still clobber your page cache, and do more seeks than a simpler file-hashing solution would




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



Notes / warnings:
=====
* think about what your delete rules mean. It'll refuse to delete every copy, but you can still make a mess for yourself.
* I have done basic sanity tests, but don't trust this blindly on files you haven't backed up.

* Does not consider symlinks readable files, so won't delete them or consider them duplictes of the things they point to.
* ...but note it can still _break_ symlinks (to not do that, it have to scan the entire filesystem)

* safe around hardlinks in that it avoids adding the same inode twice. There is no space to be saved, and you're probably hardlinking for a reason. (We could still report them, though)

* you may wish to check files between e.g. 1MB and 2MB, then 100KB and 1MB, and so on, because if you run one such subrange repeatedly (looking at the report), most data will still be in the page cache and you won't clobber that cache as fast



TODO:
=====
* test on windows

* rethink the delete rules. There's much more logic beneath all this, but it's nontrivial to use so I took most of it out (of the options)
* maybe rip out the rules after all? (I usually look at the output and delete manually)

* cleanup

* More sanity checks, and regression tests. I _really_ don't want to have to explain that we deleted all your files due to a silly bug  :)

* figure out why the 'total read' sum is incorrect



CONSIDERING:
* progress bar for larger files

* page-cache-non-clobbering (posix_fadvise(POSIX_FADV_DONTNEED), though it's only in os since py3.3)

* hardlink duplicate files that are on the same filesystem

* consider a homedir config of permant rules (for things like "always keep stuff from this dir")

* consider having an IO thread (minor speed gains?)

* storing a cache with (fullpath,mtime,size,hash(first64kB)) or so in your homedir,
  for incremental checks will much less IO, particularly on slowly growing directories
  (storage should be on the order of ~35MB per 100k files, acceptable for most)

* --generate-ruleset   interactively generate a rule file based on common patterns in a set of files
