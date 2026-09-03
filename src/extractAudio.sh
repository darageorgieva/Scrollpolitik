#!/usr/bin/env bash
#this specifies to look for "bash" in the user's "env", which is safer than just assuming a location of "bash"

set -u  #enable errors for unknown filenames

#initialize variables, in bash we cannot use spaces around "="
INPUT_DIR="../data/mp4"
OUTPUT_DIR="../data/mp3"

NO_AUDIO_FILE="../data/mp4/no_audio.txt"
CONVERSION_ERR_FILE="../data/mp4/conversion_error.txt"

#create or overwrite the two files:
#":" is a no-op command. ">" tells bash to overwrite the file with that
: > "$NO_AUDIO_FILE"
: > "$CONVERSION_ERR_FILE"

mkdir -p "$OUTPUT_DIR"  #  the "$" is used to access variables. -p means: "only create the dir if it's not already there and throw no errors if that is the case"
#why do we need quotes ""? Because filepaths can contain spaces. Without "", bash will see a name with a space in the middle as two names

for file in "$INPUT_DIR"/*.mp4; do
    [ -f "$file" ] || continue  #try to run the 1st command ([ -f "$file" ]), OR (||) if that fails, run the 2nd command ("continue"), which goes to the next iteration if a file is not a regular file

    filename="$(basename "$file" .mp4)" #extract the filename, e.g. "./video/test.mp4" becomes "test". Worth Noting: "()" is a command substitution -> it runs the basename command and substitutes the result here
    output="$OUTPUT_DIR/$filename.mp3"  #concatenate to get output filepath

    # Check whether the file actually contains an audio stream
    #"if" in bash doesn't evaluate a condition, but rather the exit code of a command (here the ffprobe command). Convention: exit=0 -> success. exit!=0 -> failure!
    if ! ffprobe -v error \
        -select_streams a:0 \
        -show_entries stream=codec_name \
        -of default=noprint_wrappers=1:nokey=1 \
        "$file" >/dev/null 2>&1; then   ##>/dev/null means -> send the output to "/dev/null", which is a convention for throwing the output away (dev/null is an empty device)
        echo "$filename">>"$NO_AUDIO_FILE"  #note that we have to use ">>", not just ">" because we want to append, NOT overwrite!
        echo "NO AUDIO: $file"
        continue    #continue to next file
    fi

    if [ -f "$output" ]; then
        echo "Skipping (already exists): $filename"
        continue
    fi

    echo "Converting: $filename"

    if ffmpeg -hide_banner -loglevel error \
        -i "$file" \
        -vn \
        -map 0:a:0 \
        -c:a libmp3lame \
        -q:a 2 \
        "$output"; then
        echo "  ✓ Done"
    else
        echo "$filename">>"$CONVERSION_ERR_FILE"
        echo "  ✗ FAILED: $filename" >&2
        rm -f "$output"
    fi
done

echo "Finished."
