all: unittest build check_convention

clean:
	sudo rm -fr build images.fortests

UNITTESTS=$(shell find rackattack -name 'test_*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
COVERED_FILES=rackattack/common/hoststatemachine.py,rackattack/common/hosts.py,rackattack/virtual/alloc/allocations.py,rackattack/virtual/alloc/allocation.py,rackattack/virtual/alloc/freepool.py
unittest:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. coverage run -m unittest $(UNITTESTS)
	coverage report --show-missing --rcfile=coverage.config --fail-under=91 --include=$(COVERED_FILES)

WHITEBOXTESTS=$(shell find tests -name 'test?_*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
whiteboxtest_nonstandard:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. python -m unittest $(WHITEBOXTESTS)

testone:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. python tests/test$(NUMBER)_*.py

check_convention:
	pep8 rackattack --max-line-length=109

.PHONY: build
build: build/rackattack.virtual.egg

build/rackattack.virtual.egg: rackattack/virtual/main.py
	-mkdir $(@D)
	python -m upseto.packegg --entryPoint=$< --output=$@ --createDeps=$@.dep --compile_pyc --joinPythonNamespaces
-include build/rackattack.virtual.egg.dep

install: build/rackattack.virtual.egg
	-sudo systemctl stop rackattack-virtual.service
	-sudo mkdir /usr/share/rackattack.virtual
	sudo cp build/rackattack.virtual.egg /usr/share/rackattack.virtual
	sudo cp rackattack-virtual.service /usr/lib/systemd/system/rackattack-virtual.service
	sudo systemctl enable rackattack-virtual.service
	if ["$(DONT_START_SERVICE)" == ""]; then sudo systemctl start rackattack-virtual; fi

uninstall:
	-sudo systemctl stop rackattack-virtual
	-sudo systemctl disable rackattack-virtual.service
	-sudo rm -fr /usr/lib/systemd/system/rackattack-virtual.service
	sudo rm -fr /usr/share/rackattack.virtual
