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

