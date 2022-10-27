duppy
================

Duplicate file detection.

Will only check within file sets with the same size, which can skip a good portion of files before starting to read contents.

Within same-sized sets, we read small-to-moderate-sized blocks of content at a time, mostly because many unique files are unique in the first few dozen kilobytes, so most cases are decided with minimal reading.

On a set of largeish, mostly-unique files, we end up reading no more than a few percent of the file contents.
<br/><br/> 

That said, there are cases where this approach doesn't help much, e.g.
- for many tiny files we actually read most data, in potentially about as many operations, and are more bound more by overhead in syscalls and filesystem (also the initial treewalk), on platter drives also incurring more seek latency
- for many same-sized files, we don't eliminate any up front, and still read the start of every one
- for many large identical files, we have to read all their contents (though that's unavoidable with any method that doesn't store anything, and generally rare)


Notes / warnings:
=====
* safe around hardlinks, in that it avoids adding the same inode twice. There is no space to be saved, and you're probably hardlinking for a reason. (We could still report them, though)

* Skips symlinks - Again, no space to be saved, we we do not consider them to be files. (Also avoids having to avoid symlink loops)
  * note that we can can still _break_ symlinks, because we don't know what links to the files we're working on (and we couldn't without scanning absolutely all mounted filesystems)




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



Examples:
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

* When you have many files, you can consider checking size ranges may help, e.g. all files over 200MB, then between 10MB and 200M, then everything under 10MB. This gives you the large space savings first. Also, if you do repeat runs, this will serve a lot from page cache instead of disk. 

        duppy -s 200M         /data/varied
        duppy -s 10M  -S 200M /data/varied
        duppy -S 10M          /data/varied
        



Optional: delete logic
=====

I usually inspect and do `rm` manually.  That way mistakes are at least my own damn fault.
<br/><br/>

However, in some cases you can express bulk removal in rules, such as by path substring:
```
duppy . -d -n --keep-path=main_store/ --delete-path=just_downloaded/
```

The idea is that 
* within each set of duplicate files, each file has to be marked as DELETE, KEEP - or if no rule applies is left marked UNKNOWN.

* We only ever act on any that are considered decided

* Each set is considered 
  * undecided if they have any UNKNOWNs - because you probably want to tweak your rules, and/or leave this for a later pass
  * undecided if they have only files marked DELETE - we should always refuse to delete every copy
  * undecided if they have only files marked KEEP - could consider that deciding to do nothing. Semantics.
  * decided if they have >1 KEEP and >1 DELETE and 0 UNKNOWNs

For example:

```
DECIDED set
For set (size 1173140):
  KEEP  'fonts/googlefonts/apache/droidsansjapanese/DroidSansJapanese.ttf'
  DELE  'fonts/unsorted/droid/DroidSansJapanese.ttf'

Undecided set (only keeps)
For set (size 742076):
  KEEP  'fonts/mostlysil/CharisSILLiteracyAmArea-5.000/documentation/CharisSIL-features.pdf'
  KEEP  'fonts/mostlysil/CharisSILMali-5.000/documentation/CharisSIL-features.pdf'
  KEEP  'fonts/mostlysil/CharisSILAmArea-5.000/documentation/CharisSIL-features.pdf'

DECIDED set
For set (size 306788):
  KEEP  'fonts/googlefonts/apache/notosans/src/NotoSans-Regular-orig.ttf'
  DELE  'fonts/unsorted/noto/NotoSans-Regular.ttf'
  KEEP  'fonts/Noto/NotoSans-Regular.ttf'
  KEEP  'fonts/googlefonts/apache/notosans/NotoSans-Regular.ttf'
```

Notes:
* you generally want to start with -d -n, where -n means dry-run, which only tells you what it would do (TODO: make dry run the default, and have a "yes actually do it, I know what I'm doing" option)

* --elect-one-random is easy to run on an unstructured store. But keep in mind you can can easily make a mess for yourself when deleting randomly from structured directories.

* Standard disclaimer: While I have done basic sanity tests, and am brave enough to run this on my own filesystem, you may want a backup and not run this on your only copy of something important.



TODO:
=====
* make sameline() test for ANSI capability intead of assuming it

* make dry run the default, and have a "yes actually do it, I know what I'm doing" option

* rethink the delete rules. There's much more logic beneath all this, but if it takes too much reading and thinkig for the person who wrote it, ehhh.
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



