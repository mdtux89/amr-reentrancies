#!/bin/bash

PREFIX=$1
#input
GRAPHS=$PREFIX
PREDS=$PREFIX".parsed"
#output
ALIGNMENTS=$PREFIX".alignments"

cat "$GRAPHS" | perl -ne 's/^#.*\n//g; print;' | tr '\t' ' ' | tr -s ' ' > 1.tmp
cat "$PREDS" | perl -ne 's/^#.*\n//g; print;' | tr '\t' ' ' | tr -s ' ' > 2.tmp
python2 smatch/smatch.py -f $GRAPHS $PREDS -a | head -n -1 > $ALIGNMENTS
rm 1.tmp
rm 2.tmp
