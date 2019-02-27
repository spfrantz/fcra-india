#!/bin/bash
# Verify PDF integrity using pdftk
# Adapted from:
#  https://superuser.com/questions/580887/check-if-pdf-files-are-corrupted-using-command-line-on-linux

FILE=$1
for f in "$1";
        do
                if pdftotext "$f" &> /dev/null; then
                        : Nothing
                else
                        echo broken;
                fi
done
