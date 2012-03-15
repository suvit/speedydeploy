#!/bin/sh
export LANG='en_US.UTF-8'
export LC_ALL='en_US.UTF-8'
exec ./{{project}}.fcgi "$@"
