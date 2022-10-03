#!/bin/sh

if [ "$TRADING_MODE" = "paper" ]; then  
  port="4002"
else
  port="4001"
fi

if netstat -talpn | grep --line-buffered -q ":$port "; then
    echo "Error: Found an open TCP connection on $port already, unable to setup socat.\n Exiting 1"
    exit 1
fi