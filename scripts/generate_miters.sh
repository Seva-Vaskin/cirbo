#!/bin/bash

ABC_EXEC=$1

if [ -z "$ABC_EXEC" ]; then
    echo "Usage: $0 <path_to_abc_executable>"
    exit 1
fi

if [ ! -x "$ABC_EXEC" ]; then
    echo "Error: ABC executable not found or not executable at $ABC_EXEC"
    exit 1
fi

# Create output directories
mkdir -p data/sat/miters/mul
mkdir -p data/sat/miters/sort

echo "Processing Multipliers..."
# Loop through indices 1 to 20
for i in {1..20}; do
    # Find all files ending with _${i}.bench
    # Use array to capture filenames
    files=(data/sat/mul/mul_*_${i}.bench)
    
    # Check if files exist (glob expands to itself if no match in default bash)
    if [ ! -e "${files[0]}" ]; then
        continue
    fi

    count=${#files[@]}
    if [ "$count" -lt 2 ]; then
        # Need at least 2 to make a pair
        continue
    fi

    echo "Index $i: Found $count files. Generating pairs..."

    for ((j=0; j<count; j++)); do
        for ((k=j+1; k<count; k++)); do
            f1="${files[j]}"
            f2="${files[k]}"
            
            n1=$(basename "$f1" .bench)
            n2=$(basename "$f2" .bench)
            
            # Extract common prefix and differing parts
            # Pattern: mul_TYPE_INDEX.bench
            # We want: mul_INDEX_TYPE1_vs_TYPE2.aig
            
            # Extract index (number after last underscore)
            idx=$(echo "$n1" | awk -F_ '{print $NF}')
            
            # Extract type (between mul_ and _INDEX)
            t1=$(echo "$n1" | sed -E "s/mul_(.*)_${idx}/\1/")
            t2=$(echo "$n2" | sed -E "s/mul_(.*)_${idx}/\1/")
            
            out="data/sat/miters/mul/mul_${idx}_${t1}_vs_${t2}.aig"
            
            # Run ABC to create miter
            # read: reads the file (auto-detects format usually)
            # miter: creates miter with the network in the file
            # write: writes result as aig
            "$ABC_EXEC" -c "read $f1; miter -n $f2; write $out" > /dev/null 2>&1
        done
    done
done

echo "Processing Sorters..."
# Identify unique suffixes N_M
# Sorters are format: Type_N_M.aig
# We want: sort_N_M_Type1_vs_Type2.aig
# Extract N_M suffix from filenames
suffixes=$(find data/sat/sort -name "*.aig" | sed -E 's/.*_([0-9]+_[0-9]+)\.aig/\1/' | sort | uniq)

for s in $suffixes; do
    files=(data/sat/sort/*_${s}.aig)
    
    if [ ! -e "${files[0]}" ]; then continue; fi
    
    count=${#files[@]}
    if [ "$count" -lt 2 ]; then continue; fi
    
    echo "Suffix $s: Found $count files. Generating pairs..."
    
    for ((j=0; j<count; j++)); do
        for ((k=j+1; k<count; k++)); do
            f1="${files[j]}"
            f2="${files[k]}"
            
            n1=$(basename "$f1" .aig)
            n2=$(basename "$f2" .aig)
            
            # Extract type (everything before _N_M)
            t1=$(echo "$n1" | sed -E "s/_(.*)_${s}//")
            t2=$(echo "$n2" | sed -E "s/_(.*)_${s}//")
            
            # Handle cases where type might be at start (e.g. BubbleSort_10_4)
            # t1/t2 will hold "BubbleSort" etc.
            t1=${n1%_$s}
            t2=${n2%_$s}
            
            out="data/sat/miters/sort/sort_${s}_${t1}_vs_${t2}.aig"
            
            # For AIGs, we output AIG
            "$ABC_EXEC" -c "read $f1; miter -n $f2; write $out" > /dev/null 2>&1
        done
    done
done

echo "Done."

