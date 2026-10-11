#!/bin/bash

INPUT=${INPUT:-/pnfs/e1039/scratch/users/$USER/DimuAnaRUS/mc_gen}
OUT=${1:-./merged}
TUNES=${2:-$(for i in $(seq -w 1 30); do printf "tune%s " $i; done)}
NAME=${NAME:-RUS.root}

command -v hadd >/dev/null || { echo "hadd not found, source ../setup.sh first"; exit 1; }
mkdir -p "$OUT"

for t in $TUNES; do
    dest=$OUT/DY_$t.root
    if [ -e "$dest" ]; then echo "$t: $dest exists, skipped"; continue; fi
    files=()
    nbad=0
    for d in "$INPUT"/DY_$t/*/out; do
        f=$d/$NAME
        if [ -s "$f" ]; then files+=("$f"); else nbad=$((nbad + 1)); fi
    done
    if [ ${#files[@]} -eq 0 ]; then echo "$t: no output files found"; continue; fi
    echo "$t: merging ${#files[@]} files ($nbad missing or empty)"
    # -f overwrites, -k skips corrupt inputs instead of aborting
    hadd -f -k "$dest" "${files[@]}" > "$OUT/hadd_$t.log" 2>&1 || echo "$t: hadd reported a problem, see $OUT/hadd_$t.log"
done

ls -lh "$OUT"/DY_tune??.root 2>/dev/null
