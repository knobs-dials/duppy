duppy
================


Duplicate file detector, that incrementally checks blocks of content. 


This is generally faster (in a sight-unseen utility) than a complete-hash solution,
particularly on large files. 

...except if there _are_ a lot of large duplicates, because we spend most time verifying that. (You can make it assume after a while.)



Less if we skip smaller files like above, which makes for faster estimates of how much
space you can approximately save. For example

```
    # duppy -v -s 1M /dosgames

    Creating list of files to check...
       no file arguments given, using current directory
    Done scanning, found 7984 files to check.

    Looking for duplicates...
    ^CCtrl-C, summarizing what we have so far...
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
      Found 652 sets of duplicate files
        1271 files could be removed,
        to save 766MB
      Spent 49 seconds    reading 1.5GB  (4.7% of 33GB)
```



The motivation came from a few observations, 
mainly that distinct files are usually unique in the first few dozen KB,
and that duplicate detection is largely IO-bound.

For most of my own real test cases (e.g. image and music collection) it reads between 0.1% and 10% of the data.


Should be safe around symlinks (avoids following) and hardlinks (avoids adding the same inode twice - though it wouldn't matter much if we did).


WARNING: 
- does not consider symlinks to files we would delete (because to guarantee that, you have to scan _everything_)
- I have done basic tests, but don't trust this blindly.
- think about what your delete rules mean. It'll refuse to delete every copy, but you can still make a mess for yourself.


Also, it stands a lot of cleaning. It has since always, which is the main reason I kept on not releasing.
...this is self-manipulation, now I have to clean it up to not look as bad :P


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
          These judgments are combined conservatively, so e.g. KEEP+DELETE = KEEP

        We only delete files from decided sets,  which are those with at least one KEEP and no UNKNOWN
          Note that we *never* deletes everything: an all-DELETE set is considered undecided)
           and that combining rules tends to be on the conservative side.


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

* cleanup


* think about the clarity of the rules

* consider a homedir config of permant rules (for things like "always keep stuff from this dir")


* consider storing a cache with (fullpath,mtime,size,hash(first64kB)) or so in your homedir,
  for incremental checks on slowly growing directories
  (storage should be on the order of ~35MB per 100k files, acceptable for most)

* consider having an IO thread (minor speed gains?)


* test on windows

