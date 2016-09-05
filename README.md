duppy
================


Duplicate file detector.

Incrementally checks blocks of content, motivated by the observation that duplicate detection is largely IO-bound,
and since distinct files are usually unique in the first few dozen KB, the larger the files, the less efficient a complete-hash solution is (...when you don't store and use information about the files it has seen. I'm considering that in here.).

...except if there _are_ a lot of large duplicates, because you still have to spend much of your time verifying.


You can make it assume after some amount of bytes. 
If you want a faster faster-yet-more-approximate estimate of possible space savings, do that, and ignore smaller files.
For example,

```
    # duppy -v -a 32M -s 500K /dosgames
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
* Should be safe around symlinks (avoids following) and hardlinks (avoids adding the same inode twice - though it wouldn't matter much if we did).
* ...but does not consider that symlink may be pointing at files we are deleting (because to guarantee that, you have to scan the entire filesystem)
* I have done basic sanity tests, but don't trust this blindly on files you haven't backed up.
* think about what your delete rules mean. It'll refuse to delete every copy, but you can still make a mess for yourself.


Options
===
```
    Usage: duppy [options] path [path...]

       Finds duplicate files.

       By default only prints a summary of wasted space.
       Use -v for a full list of duplicates (I feel more comfortable manually deleting based on this output)
        or -d and some rules to automate deletion.

       Options:
          -q             be quiet while working.   Access errors are still reported.
          -v             be verbose about progress, report all duplicate file sets. Specify twice for even more.

          -R             Non-recursive.
                         (To run on only files in curdr -R,  and * (not .) for the argument)

          -s size    minimum size. Ignore files smaller than this size.  Default is 1, only ignores zero-length files.
                     (useful to find major space saving in less time)
          -S size    maximum size
                     (sometimes useful in a "now look at just the files between 100KB and 200KB",
                      which makes repeated runs faster since most data will still be cached)

          -a size    Assume a set is identical after this many matching bytes, e.g.  -a 32MB
                     Meant for dry-runs, for a faster _estimation_ of wasted space,
                     but WARNING: it will also apply to real runs. While this _usually_ makes sense
                     (most files that are distinct are so within ~150KB), *know for sure* that it makes sense for your case.


       Rules and deleting:
          --rule-help            List of rules, and examples of use.
          -n                     Apply rules - in a dry run. Will say what it would do, but delete nothing.
          -d                     Apply rules, and delete files from sets that are marked DELETE (and that also have at least one KEEP).

       Examples:
          # Just list what is duplicate
          duppy -v .

          # faster estimation of bulk space you could probably free  (note: not a full check)
          duppy -v -s 10M -a 20M /data/Video

          # work on the the specific files we mention, and no recursion
          duppy -vR *
```


Delete rule options (still sort of an experiment)
===
```
        The set is currently
            --elect-one-random                      keep one, the easiest and most arbitrary way to go.
            --(keep,delete,lose)-path=SUBSTR        match absolute path by substring
            --(keep,delete,lose)-path-re=REGEXP     match absolute path with regular expressions, mark any matches KEEP
            --(keep,delete,lose)-newest             looks for file(s) with the most recent time  (and for each file uses max(mtime,ctime))
            --(keep,delete,lose)-deepest            keep file in deepest directory.   Useful when you typically organize into directories.
            --(keep,delete,lose)-shallowest         keep file in shallowest directory. Useful in similar cases.
            --(keep,delete,lose)-longest-path       considers string length of full path
            --(keep,delete,lose)-longest-basename   considers string length of just the filename (not the path to the directory it is in)

        lose-*   rules mark matches DELETE, non-matches as KEEP     so by themselves they are decisive
        delete-* rules mark matches DELETE, non-matches UNKNOWN     e.g. useful if combining a detailed set of keep- and delete-
        keep-*   rules mark matches KEEP, non-matches UNKNOWN,      e.g. useful to mark exceptions to a main lose- rule

        We apply all specified rules to all sets, which marks each filename as KEEP, DELETE, or UNKNOWN.
          These are combined conservatively, e.g. KEEP+DELETE = KEEP

        We only delete files from decided sets,  which are those with at least one KEEP and no UNKNOWN
          Note that we *never* delete everything: an all-DELETE set is considered undecided)


     Examples:

          # "I don't care which version you keep"
          duppy -v -d -n --keep-one-random /data/Video

          # "Right, I just downloaded a load of images, and I have most already. Clean from this new dir"
          duppy -v -d -n --delete-path '/data/images/justdownloaded/' /data/images

          # "assume that anything sorted into a deeper directory, and anything named archive, needs to stay"
          # This may well be indecisive for some sets
          duppy -v -d -n --keep-deepest --keep-path-re '[Aa]rchive' /data/Video
```





TODO:
=====
* consider verbosity by default (I always use -v)

* maybe rip out the rules after all? (I usually look at the -v output and delete manually)

* More sanity checks, and regression tests. I _really_ don't want to have to explain that we deleted all your files due to a silly bug  :)

* figure out why the 'total read' sum is incorrect

* cleanup. Until now I mainly didn't release it because it needed cleaning. Typical :)


* think about the clarity of the rule system

* consider a homedir config of permant rules (for things like "always keep stuff from this dir")


* consider storing a cache with (fullpath,mtime,size,hash(first64kB)) or so in your homedir,
  for incremental checks on slowly growing directories
  (storage should be on the order of ~35MB per 100k files, acceptable for most)

* consider having an IO thread (minor speed gains?)


* test on windows

