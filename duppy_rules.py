#!/usr/bin/python

'''
    These functions take a set of (absolute) filenames,
    and decide which to keep and which to delete,
    by returning a dict that maps every member to KEEP, DELE, or UNKN.

    This to be able to combine multiple rules sensibly.


    There is extra logic to actually deciding.
    - usually   you want to not do anything when all are DELE
    - sometimes you want to not do anything when there are any UNKN
'''
# avoid using globals, this is import *'d elsewhere

import os
import re
import random

# not: min() and max() have meaning
KEEP = 2
DELE = 1
UNKN = 0



    
def choose_one_random(givenset, substr=None):
    ''' Randomly marks one as keep, the rest as delete. Use only if you *really* don't care which file you keep '''
    ret = {}
    orc = random.choice(givenset)
    for fn in givenset:
        if fn==orc:
            ret[fn]=KEEP
        else:
            ret[fn]=DELE
    return ret




#def delete_default(givenset):
#    ''' meant for "keep one, have the rest already marked for deleting" logic.
#        Note that since we never choose to throw away everything, by itself this will result in undecided sets
#    '''
#    ret = {}
#    for fn in givenset:
#        ret[fn] = DELE






def keep_path(givenset, substr=None):
    ''' keep anything which matches the given substring '''
    ret = {}
    for fn in givenset:
        if substr in fn:
            ret[fn]=KEEP
        else:
            ret[fn]=UNKN
    return ret

def delete_path(givenset, substr=None, others=KEEP):
    ''' delete anything which matches the given substring '''
    ret = {}
    for fn in givenset:
        if substr in fn:
            ret[fn] = DELE
        else:
            ret[fn] = others
    return ret


def keep_path_re(givenset, restr=None):
    ''' keep anything which matches the given regexp (uses re.search) '''
    ret = {}
    rem = re.compile(restr)
    for fn in givenset:
        if rem.search(fn)!=None:
            ret[fn]=KEEP
        else:
            ret[fn]=UNKN
    return ret

def delete_path_re(givenset, restr=None, others=KEEP):
    ''' delete anything which matches the given regexp '''
    ret = {}
    rem = re.compile(restr)
    for fn in givenset:
        if rem.search(fn)!=None:
            ret[fn] = DELE
        else:
            ret[fn] = others
    return ret




def keep_deepest(givenset, others=DELE):
    ''' Keep file(s) in the deepest directory,
        By default, delete all others (the value of nondeepest)
        
        Can be useful when you sort things into deeper directories.

        Keep in mind that if there are symlinked directories,
        this decision can be arbitrary.
    '''
    ret = {}
    depths = {}
    for fn in givenset:
        l = os.path.dirname(fn).split(os.path.sep)
        depths[fn] = len(l)
    deepest_depth = max(depths.values())
    if min(depths) == deepest_depth: #all at the same depth? Then we want to have no effect:
        for fn in givenset:
            ret[fn]=UNKN
    else:
        for fn in givenset:
            if depths[fn]==deepest_depth:
                ret[fn] = KEEP
            else:
                ret[fn] = others
    return ret



def keep_shallowest(givenset, nonshallowest=DELE):
    ''' copy-paste-tweak of the above.  TODO: unify in a single function '''
    ret = {}
    depths = {}
    for fn in givenset:
        l = os.path.dirname(fn).split(os.path.sep)
        depths[fn] = len(l)
    shallowest_depth = min(depths.values())
    if min(depths) == shallowest_depth: #all at the same depth? Then we want to have no effect:
        for fn in givenset:
            ret[fn]=UNKN
    else:
        for fn in givenset:
            if depths[fn]==shallowest_depth:
                ret[fn]=KEEP
            else:
                ret[fn]=nonshallowest
    return ret



def keep_longestpath(givenset, nondeepest=DELE):
    ''' Keep the file(s) with the longest path string length.
        TODO: make this consider unicode string length, not bytestring length.
    '''
    ret  = {}    
    lens = {} # doesn't need to be a dict, but hey.
    for fn in givenset:
        lens[fn]=len(fn)
    longest_len = max(lens.values())
    
    for fn in givenset:
        if lens[fn]==longest_len:
            ret[fn]=KEEP
        else:
            ret[fn]=nondeepest
    return ret


def keep_longestbasename(givenset, nondeepest=DELE):
    ' TODO: make this consider unicode string length, not bytestring length '
    ret  = {}
    lens = {} # doesn't need to be a dict, but eh.
    for fn in givenset:
        lens[fn] = len( os.path.basename(fn) )
    longest_len = max(lens.values())
    
    for fn in givenset:
        if lens[fn]==longest_len:
            ret[fn]=KEEP
        else:
            ret[fn]=nondeepest
    return ret

    

def keep_newest(givenset, nonnewest=DELE):
    ' Keep the file(s) with the most recent ctime/mtime '
    ret   = {}    
    times = {}
    try:
        for fn in givenset:
            stob = os.stat(fn)
            times[fn] = max( stob.st_ctime, stob.st_mtime )
    except Exception as e:
        #raise
        print( "Not deciding set - could not stat(%s)"%fn)
        ret={}
        for fn in givenset:
            ret[fn] = UNKN  # not enough to always avoid a decision, but is that a bad thing?
        return ret

    newest_time = max(times.values())  
    for fn in givenset:
        if times[fn] == newest_time:
            ret[fn] = KEEP
        else:
            ret[fn] = nonnewest
    return ret
    




def default_rules():
    ''' Returns a list of default rules that _should_ protect system files and such.
        Never *count* on this stuff, though.

        TODO: move to a default-configuration file
              ...and separate out the stuff that can be ignored by the indexer
    '''
    rules = []
    
    # This stuff shouldn't be necessary
    rules.append(  ('keep:  /lib/       (system stuff)',  keep_path_re, {'restr':'/lib/'} )  )
    rules.append(  ('keep:  /bin/       (system stuff)',  keep_path_re, {'restr':'/bin/'} )  )
    rules.append(  ('keep:  /sbin/      (system stuff)',  keep_path_re, {'restr':'/sbin/'} )  )
    rules.append(  ('keep:  /boot/      (system stuff)',  keep_path_re, {'restr':'/boot/'} )  )

    rules.append(  ('keep:  /.keep      (keep-this-directory marker)', keep_path, {'substr':'/.keep$'} )  )

    #rules.append(  ('keep:  .dylib      (system stuff)',  keep_path,    {'substr':'.dylib$'} )  )
    #rules.append(  ('keep:  .so         (system stuff)',  keep_path,    {'substr':'.so$'} )  )

    # Duplicates you do want to know about, but don't want removed:
    rules.append(  ('keep:  /tmp/       (system stuff)',  keep_path_re, {'restr':'^/tmp/'} )  )
    rules.append(  ('keep:  /.svn/      (versioning metadata)',        keep_path, {'substr':'/.svn/'} )  )
    rules.append(  ('keep:  /.git/      (versioning metadata)',        keep_path, {'substr':'/.git/'} )  )
    rules.append(  ('keep:  /.bzr/      (versioning metadata)',        keep_path, {'substr':'/.bzr/'} )  )
    rules.append(  ('keep:  /.hg/       (versioning metadata)',        keep_path, {'substr':'/.hg/'} )  )

    # Metadata files which may attach identical things to distinct files
    rules.append(  ('keep:  .xmp        (metadata)', keep_path_re, {'restr':'[.]xmp$'} )  )
    rules.append(  ('keep:  .ifo        (metadata)', keep_path_re, {'restr':'[.]ifo$'} )  )
    rules.append(  ('keep:  /Picasa.ini (metadata)', keep_path_re, {'restr':'/Picasa[.]ini$'} )  )
    #rules.append(  ('keep:  /root/      (system stuff)',  keep_path_re, {'restr':'/root/'} )  )

    for keep_restr in (
        '/[Bb]ackup',
        '/[Aa]rchive',
        ):
        rules.append(  ('keep:  %s'%keep_restr,  keep_path_re,   {'restr':keep_restr} )  )

    return rules
