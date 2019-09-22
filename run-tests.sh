#!/bin/bash

cd $(dirname "$0")

python -m pytest \
	--capture=no \
	--cov-report term-missing \
	--cov=src/ \
	--ignore=vendor \
	$@
