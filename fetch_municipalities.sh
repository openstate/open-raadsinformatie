#!/bin/bash

# Function to fetch and process data for a supplier
fetch_supplier_data() {
    local supplier=$1
    echo "Supplier: $supplier"
    echo "key,cbs_id"
    curl -s "https://raw.githubusercontent.com/openstate/open-raadsinformatie/master/ocd_backend/sources/ori.$supplier.yaml" | \
    yq e '.["ori.'$supplier'"][] | [.key, .cbs_id] | @csv' | \
    sed 's/"//g'  # Remove quotes for easier Excel import
    echo
}

# Main script
echo "Fetching data for all suppliers..."
echo

for supplier in go notubiz parlaeus ibabs; do
    fetch_supplier_data $supplier
done

echo "Data fetching complete. You can now copy and paste this output into an Excel sheet."
