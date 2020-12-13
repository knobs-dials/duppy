duppy
================

Duplicate file detection.

Only checks within file sets with the same size, because when you have varied files we don't need to check some at all.

For sets we need to check, reads moderate-sized blocks of content at a time.
When you have many large mostly-unique files, we can avoid reading most contents, because most unique things are unique first few dozen kilobytes.


That said, in some cases, e.g. a large set of small files, we save no time or IO because (particularly on platter) we just become seek-bound instead of read-bound. Might even be slightly worse.  On SSD seeks are a lot cheaper so this is still better. 

(Also, a large set of large identical files will take all the reading to check. But this seems unusual, and there's an option to help there)


Example:
```
    $ duppy -s 500K -a 32M /dosgames

    NOTE: Assuming files are identical after 32MB

    Creating list of files to check...
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



Further example commands:

* Look at everything under a path, recursively:

        duppy .

* work on the the specific files we mention, and no recursion if that includes a directory

        duppy -R frames_*

* When you have many files, e.g. checking all files over 200MB, then between 10MB and 200M, then 5MB and 10MB, etc. for a quicker indication of the largest savings first 

        duppy -s 200M         /data/varied
        duppy -s 10M  -S 200M /data/varied
        duppy -s 5M  - S 10M  /data/varied
        
Working on smaller sets also makes it more likely that repeated runs on the same files is served from page cache, as we don't clobber it so quickly. This can be handy if you're dealing with the results manually. This is also why the largest files are last in the output.



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
                        to nearest KB. defaults to 256KB. Can be upped on RAID.
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




Notes / warnings:
=====
* safe around hardlinks in that it avoids adding the same inode twice. There is no space to be saved, and you're probably hardlinking for a reason. (We could still report them, though)

* Skips symlinks - does not consider them to be files, so won't delete the links or consider their content.
* ..but: it can still _break_ symlinks (and ensuring we won't would require scanning all mounted filesystems)



Delete logic
=====
* There are some parameters that assist deleting files

* which will refuse to delete every copy - but note that doesn't mean you can't make a mess for yourself

* note also -n, dry-run, which only tells you what it would do

* Example: If you find duplicates, and any of them is in a directory called justdownloaded, choose that to delete

        duppy . -d -n --delete-path=/justdownloaded/

* Example: If you find duplicates, keep a random one within the set.

        duppy . -d -n --elect-one-random /imagetorrent/

* Standard disclaimer: While I have done basic sanity tests (and am brave enough to run this on my own files), you may want a backup and not run this on your only copy of something.



TODO:
=====
* resolve symlink argument paths (only just noticed that)

* rethink the delete rules. There's much more logic beneath all this, but it should be much simpler to understand before I put that back in
* maybe rip out the rules after all? (I usually look at the output and delete manually)
* maybe consider generating a ruleset based on common patterns in a set of files?

* code cleanup

* test on windows

* More sanity checks

* regression tests

* figure out why the 'total read' sum is incorrect


CONSIDERING:
* homedir config of permanent rules (for things like "always keep stuff from this dir")

* progress bar, to give feedback when checking large files

* storing a cache with (fullpath,mtime,size,hash(first64kB)) or so in your homedir,
  as we can probably eliminate most sets from read just that file, before they hit the fs tree.
  (storage should be on the order of ~35MB per 100k files, acceptable to most uses)

* allow hardlinking duplicate files (that are on the same hardlink-supporting filesystem)

* page-cache-non-clobbering (posix_fadvise(POSIX_FADV_DONTNEED), though it's only in os since py3.3)

