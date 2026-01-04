#!/bin/bash

# Check if both arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <directory_path> <output_filename.pdf>"
    exit 1
fi

TARGET_DIR=$1
OUTPUT_FILE=$2

# 1. Check if directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist."
    exit 1
fi

# 2. Change to the directory or exit if it fails
cd "$TARGET_DIR" || exit 1

# 3. Check if any PDFs exist
# We use a nullglob-like check to avoid 'ls' errors
if ! ls *.pdf >/dev/null 2>&1; then
    echo "Error: No PDF files found in '$TARGET_DIR'."
    exit 1
fi

# 4. Merge files sorted by time (oldest first)
# We use -d '\n' to handle spaces in filenames
ls -tr *.pdf | xargs -d '\n' sh -c 'pdfunite "$@" "$0"' "$OUTPUT_FILE"

echo "Success: Merged files into $TARGET_DIR/$OUTPUT_FILE"
