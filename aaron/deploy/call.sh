#!/bin/bash
# call.sh <domain> <query-string...>   -> hits the token script through the edge
set -u
source ~/.config/fmrex/da.env
dom="$1"; shift
curl -s -k -A "Mozilla/5.0" -H "Cache-Control: no-cache" --max-time 300 \
  --resolve "$dom:443:144.217.60.100" -G "https://$dom/_boot.php" "$@" -w "\n[http %{http_code}]\n"
