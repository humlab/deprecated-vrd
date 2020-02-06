#!/usr/bin/env bash

function usage {
   cat << EOF
Usage: $0 <password>

Deploys a JupyterLab container with project pertinent notebooks
EOF
   exit 1
}

if [ $# -ne 1 ]; then
    usage;
fi

while test $# -gt 0; do
    case "$1" in
        -h|--help)
            usage;
            ;;
        *)
            break
            ;;
    esac
done

echo "Deploying notebooks using \"$1\" as the password. Please enter it when logging into Jupyter"
ACCESS_TOKEN=$(python scripts/generate_access_token.py $1) docker-compose -f notebook.yml up --build -d
