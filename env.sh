export PYTHONUNBUFFERED=1
export MINKNOW_API_USE_LOCAL_TOKEN="no" # to avoid printing a debug error message (non-fatal)
export MINKNOW_SIMULATOR="true"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CERTS_DIR=$SCRIPT_DIR/certs

export MINKNOW_TRUSTED_CA=$CERTS_DIR/server.pem
export MINKNOW_API_CLIENT_CERTIFICATE_CHAIN=$CERTS_DIR/client.pem
export MINKNOW_API_CLIENT_KEY=$CERTS_DIR/client.key
export PYTHONPATH=$PYTHONPATH:$SCRIPT_DIR
