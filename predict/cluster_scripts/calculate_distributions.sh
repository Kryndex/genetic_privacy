#!/usr/bin/env bash
set -euo pipefail

ulimit -Sv 1000000

function join { local IFS="$1"; shift; echo "$*"; }

POPULATION_DIR="$1"
POPULATION_BASE="$(basename "${POPULATION_DIR}")"
CODE_DIR="/n/fs/grad/pe5/genetic_privacy/predict"
SCRATCH_POP_DIR="/scratch/${USER}/${POPULATION_BASE}"
REMOTE_POP_DIR="/scratch/network/${USER}/${POPULATION_BASE}"
OUTPUT_DIR="/n/fs/grad/pe5/genetic_privacy_output"

echo "Population directory is ${POPULATION_DIR}"

mkdir -p "/scratch/${USER}/db"
mkdir -p "${OUTPUT_DIR}/outfiles"

cp -r "${POPULATION_DIR}" "${SCRATCH_POP_DIR}"

echo "Dividing up labeled nodes."
DIVIDE_ID=$(sbatch -o "${OUTPUT_DIR}/outfiles/slurm-%j.out" --mem=4GB \
                   --workdir="${CODE_DIR}" \
                   "divide_work.py" "${POPULATION_DIR}" 5 \
                   --num_labeled 50 --output_dir "${OUTPUT_DIR}" | \
                   grep -Eo "[0-9]+")

# Find a better way to wait for jobs
while [ $(squeue --jobs "${DIVIDE_ID}" | wc -l) -gt 1 ]
do
    sleep 2
done

echo "Assigning partitions."
JOBIDS=()
for FILENAME in ../${OUTPUT_DIR}/partition_*_labeled_nodes.pickle
do
    NUM="$(basename "$FILENAME" | grep -o -E '[0-9]+')"
    echo "Assigning group ${NUM}"
    JOBIDS+=($(sbatch -o "${OUTPUT_DIR}/outfiles/slurm-%A_%a.out"\
             remote_subset_shared.sh "${REMOTE_POP_DIR}" "$FILENAME"\
             "${OUTPUT_DIR}" "labeled_${NUM}.db" | grep -Eo "[0-9]+"))
done

# Find a better way to wait for jobs
COMMA_JOBS="$(join , "${JOBIDS[@]}")"
while [ $(squeue --jobs "${COMMA_JOBS}" | wc -l) -gt 1 ]
do
    sleep 2
done
