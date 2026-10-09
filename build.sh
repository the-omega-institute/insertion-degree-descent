#!/bin/sh
set -eu
mkdir -p bin runs
for source in audit targeted_factor symbolic symbolic_memo symbolic_last symbolic3 symbolic3_fresh structured_audit coarsenings independent_symbolic; do
    c++ -O3 -std=c++17 "$source.cpp" -o "bin/$source"
done
