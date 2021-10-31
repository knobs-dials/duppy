duppy
================

Duplicate file detection.

Only checks within file sets with the same size, because that can exclude ever reading a good portion of files.

Within those same-sized sets we need to check, we read small-to-moderate-sized blocks of content at a time, because many unique files are unique in the first few dozen kilobytes.

On a set of largeish, mostly-unique files, we can avoid reading most file contents.

That said, there are cases where this approach doesn't much, e.g.
- for many same-sized files, we still read the start of every one
- for many tiny files we are more bound more by filesystem calls, and on platter drives specifically seek speed
- for many large identical files, we have to read all their contents (though this should be a rare case, and you would probably *want* that verification in this case)

Example:
===
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

* When you have many files, you can consider checking size ranges may help, e.g. all files over 200MB, then between 10MB and 200M, then 5MB and 10MB, etc. This gives you faster indication of large duplicates first. It also more likely that repeated runs on the same files is served from page cache, as we don't clobber it as quickly. 

        duppy -s 200M         /data/varied
        duppy -s 10M  -S 200M /data/varied
        duppy -s 5M  - S 10M  /data/varied
        


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
* safe around hardlinks, in that it avoids adding the same inode twice. There is no space to be saved, and you're probably hardlinking for a reason. (We could still report them, though)

* Skips symlinks - does not consider them to be files, so won't delete the links or consider their content.
* ..but: it can still _break_ symlinks because we don't know what links to the files weo're working on (and we couldn't, without scanning all mounted filesystems)



Delete logic
=====
* There are some parameters that assist deleting files

* which will refuse to delete every copy - but note that doesn't mean you can't make a mess for yourself

* note also -n, dry-run, which only tells you what it would do

* Example: If you find duplicates, and any of them is in a directory called justdownloaded, choose that to delete

        duppy . -d -n --delete-path=/justdownloaded/

* Example: If you find duplicates, keep a random one within the set.

        duppy . -d -n --elect-one-random /downloadedpictures/

* Standard disclaimer: While I have done basic sanity tests, and am brave enough to run this on my own filesystem, you may want a backup and not run this on your only copy of something important.



TODO:
=====
* resolve arguments that are symlinks

* rethink the delete rules. There's much more logic beneath all this, but it should be much simpler to understand before I put that back in
  * maybe rip out the rules after all? (I usually look at the output and delete manually)
  * maybe consider generating a ruleset based on common patterns in a set of files?

* code cleanup

* more sanity checks

* regression tests

* figure out why the 'total read' sum is incorrect

* test on windows

* see what link/inode stuff means when the underlying filesystem API is mapped to Windows's


CONSIDERING:
* storing a cache with (fullpath,mtime,size,hash(first64kB)) or so in your homedir,
  meaning that a slowly changing fileset could eliminate most cases from just that file,
  before they hit the fs tree.
  (storage should be on the order of ~35MB per 100k files, acceptable to most uses)

* homedir config of permanent rules (for things like "always keep stuff from this dir")

* progress bar, to give feedback when checking large files

* allow hardlinking duplicate files (that are on the same hardlink-supporting filesystem)

* page-cache-non-clobbering (posix_fadvise(POSIX_FADV_DONTNEED), though it's only in os since py3.3)


See also:
=====
* [rdfind](https://github.com/pauldreik/rdfind) also eliminates a bunch of options up front and with minimal reading



