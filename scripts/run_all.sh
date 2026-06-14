#!/bin/bash
set -e

cd "$(dirname "$0")"  # ensure we're in agent-o

# activate venv if you want this automated:
# source venv/bin/activate

echo "Current directory: $(pwd)"
for folder in ../crews/*; do
    if [ -d "$folder" ]; then
        echo "Analyzing: $folder"
        python3 run_prompt.py "$folder"
        #break  # remove this line once you're happy with the first run
    fi
done
