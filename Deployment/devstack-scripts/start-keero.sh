#!/bin/bash

if [[ -z "$1" ]] ; then
    source ./localrc
fi

die_if_not_set INSTALL_DIR

# Starting Portas
#================
if [[ ! -d "$INSTALL_DIR/portas" ]] ; then
    mkdir -p "$INSTALL_DIR/portas"
fi

cp "$INSTALL_DIR/keero/portas/etc" "$INSTALL_DIR/portas/etc"

screen_it portas "cd $INSTALL_DIR/portas && portas-api --config-file=$INSTALL_DIR/portas/etc/portas-api.conf"
#================



# Starting Conductor
#===================
screen_it conductor "cd $INSTALL_DIR/keero/conductor && bash ./tools/with_venv.sh ./bin/app.py"
#===================
