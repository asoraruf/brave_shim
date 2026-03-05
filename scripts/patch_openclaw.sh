#!/bin/bash

OPENCLAW_NODE_MOD_PATH=/usr/lib/node_modules/openclaw

# ---- Do not edit below this line ----

for file_to_patch in $( grep -r "https://api.search.brave.com" ${OPENCLAW_NODE_MOD_PATH} | cut -d ':' -f1)
do
   cp -a ${file_to_patch} ${file_to_patch}.bck
   sed -i "s#https://api.search.brave.com/#http://127.0.0.1:8000/#g" ${file_to_patch}
done

openclaw gateway restart
