#!/bin/bash
#
# Example of how to chain MapReduce jobs together.  The output of one
# job is the input to the next.
#
# Madoop options
# -input <directory>                            # Input directory
# -output <directory>                           # Output directory
# -mapper <exec_name>                           # Mapper executable
# -reducer <exec_name>                          # Reducer executable
# -partitioner <exec_name>                      # Optional: Partitioner executable

# Stop on errors
# See https://www.shkodenko.com/what-string-set-eeuo-pipefail-in-shell-script-does-mean/
set -Eeuo pipefail

# Optional input directory argument
PIPELINE_INPUT=crawl
if [ -n "${1-}" ]; then
  PIPELINE_INPUT="$1"
fi

# Print commands
set -x

# Remove output directories
rm -rf output output[0-9]

# Job 0: Document Count (this job is not part of the pipeline)
madoop \
  -input ${PIPELINE_INPUT} \
  -output output0 \
  -mapper ./map0.py \
  -reducer ./reduce0.py

# Copy document count to a separate file
cp output0/part-00000 total_document_count.txt

# Job 1: Parsing
madoop \
  -input ${PIPELINE_INPUT} \
  -output output1 \
  -mapper ./map1.py \
  -reducer ./reduce1.py

# Job 2: Build term statistics and posting lists
madoop \
  -input output1 \
  -output output2 \
  -mapper ./map2.py \
  -reducer ./reduce2.py

# Job 3: Partition final inverted index by doc_id % 3
madoop \
  -input output2 \
  -output output \
  -mapper ./map3.py \
  -reducer ./reduce3.py \
  -partitioner ./partition.py

rm -rf ../index_server/index/inverted_index
mkdir -p ../index_server/index/inverted_index
cp output/part-00000 ../index_server/index/inverted_index/inverted_index_0.txt
cp output/part-00001 ../index_server/index/inverted_index/inverted_index_1.txt
cp output/part-00002 ../index_server/index/inverted_index/inverted_index_2.txt


