#!/bin/bash
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
cd ./usr/lib/astronciaiptv/
env python3 -m astroncia_iptv
exit "$?"
