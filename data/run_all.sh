#!/bin/bash
{
set -euo pipefail

# Get the directory where this script is located
# Copied from <http://stackoverflow.com/a/246128/1166306>
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$SCRIPT_DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"


# These functions just makes things pretty.
text_highlight() { (tput setab 3; tput setaf 0) 2>/dev/null || true; } # tput will fail on bad terminals, but that's okay
text_default() { tput sgr0 2>/dev/null || true; }
run() {
    # On OSX, if I print a newline while still in highlight-mode, the whole next line gets colored, and then partially un-colored as the next command overwrites it.
    # So, Here I put the newline _after_ the text_default.
    echo; text_highlight; echo -n "=> Starting $1"; text_default; echo
    start_time=$(date +%s)
    set +e
    $SCRIPT_DIR/$1
    exit_code=$?
    set -e
    end_time=$(date +%s)
    text_highlight; echo -n "=> Completed $1 in $((end_time - start_time)) seconds with exit code $exit_code"; text_default; echo
    [[ $exit_code = 0 ]] || exit $exit_code
}

# run ./0_0_make_phenolist.sh
run ./0_1_get_cpras_from_each_input_file.py # TODO: check dates of src_filenames (hard from Makefile, maybe easiest from python. snakemake?)
run ./0_2_get_cpras_to_show.py # TODO: check dates of cpra/*
run ./1_2_download_rsids.sh
run ./1_3_download_genes.sh
run ./1_4_add_rsids.py
run ./1_5_add_nearest_genes.py
run ./1_8_make_tries.py
run ./3_1_standardize_each_pheno.py # TODO: each depends on its own src_filename, and also on sites.tsv
run ./3_2_make_manhattan_for_each_pheno.py # TODO: each depends on its own augmented_pheno
run ./3_3_make_QQ_for_each_pheno.py # TODO: each depends on its own augmented_pheno
run ./4_1_make_matrix.sh # TODO: depends on augmented_pheno/*
run ./4_2_bgzip.sh
run ./5_1_bgzip_augmented_phenos.sh # TODO: each depends on its own augmented_pheno
run ./9_3_get_all_hits.py
# TODO: delete unneeded files?
}