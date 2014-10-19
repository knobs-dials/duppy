duppy
================

Duplicate file detector. 

Uses an incremental block checker that in many cases avoids a
considerable amount of IO compared to, say, a match-complete-hash implementation.

TODO:
- thinking about how to conveniently deal with a large number of 
  duplicates automatically
- near-duplicate matches for text
- near-duplicate matches for images
- near-duplicate matches for music

Screenshot: 

![duppy screenshot](http://helpful.knobs-dials.com/images/duppy.png)