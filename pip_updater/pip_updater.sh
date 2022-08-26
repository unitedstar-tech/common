#!/bin/bash
export LANG=C
if [ -n "$1" ]
then
	python=$1
else
	python=`which python3`
fi
$python --version
$python -m pip install -U pip
num=`$python -m pip list -o | wc -l`
num=`expr $num - 2`
packages=(`$python -m pip list -o | tail -$num | awk '{print $1}'`)
for i in ${packages[@]}
do
	$python -m pip install -U $i || continue
done
