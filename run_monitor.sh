#!/bin/bash
# Dit script wordt elke 5 minuten door launchd gedraaid

# Onderdruk de onschuldige urllib3/OpenSSL-waarschuwing
# (vervuilt anders elke 5 minuten het foutenlog)
export PYTHONWARNINGS="ignore:urllib3 v2 only supports OpenSSL"

cd "/Users/miquel/Claude appjes/Privé/antikraak-monitor"

# Houd logbestanden klein: als een log meer dan 4000 regels heeft,
# bewaar dan alleen de laatste 2000 regels
for LOGBESTAND in monitor.log launchd_out.log launchd_err.log; do
    if [ -f "$LOGBESTAND" ]; then
        REGELS=$(wc -l < "$LOGBESTAND")
        if [ "$REGELS" -gt 4000 ]; then
            tail -n 2000 "$LOGBESTAND" > "$LOGBESTAND.tmp"
            cat "$LOGBESTAND.tmp" > "$LOGBESTAND"
            rm -f "$LOGBESTAND.tmp"
        fi
    fi
done

/usr/bin/python3 monitor.py
