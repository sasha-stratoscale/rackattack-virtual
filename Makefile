all: test build check_convention

clean:
	sudo rm -fr build images.fortests

test: unittest whiteboxtest
UNITTESTS=$(shell find rackattack -name 'test_*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
COVERED_FILES=rackattack/common/hoststatemachine.py,rackattack/common/hosts.py,rackattack/virtual/alloc/allocations.py,rackattack/virtual/alloc/allocation.py,rackattack/virtual/alloc/freepool.py
unittest:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. coverage run -m unittest $(UNITTESTS)
	coverage report --show-missing --rcfile=coverage.config --fail-under=91 --include=$(COVERED_FILES)

WHITEBOXTESTS=$(shell find tests -name 'test_*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
whiteboxtest:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. python -m unittest $(WHITEBOXTESTS)

testone:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. python tests/test$(NUMBER)_*.py

check_convention:
	pep8 rackattack --max-line-length=109

.PHONY: build
build: build/rackattack.virtual.egg

-include build/rackattack.virtual.egg.dep
build/rackattack.virtual.egg:
	-mkdir $(@D)
	python -m upseto.packegg --entryPoint rackattack/virtual/main.py --output=$@ --createDeps=$@.dep --compile_pyc --joinPythonNamespaces

install: build/rackattack.virtual.egg
	-sudo systemctl stop rackattack-virtual
	-sudo mkdir /usr/share/rackattack.virtual
	sudo cp build/rackattack.virtual.egg /usr/share/rackattack.virtual
	sudo cp rackattack-virtual.service /usr/lib/systemd/system/rackattack-virtual.service
	sudo systemctl enable rackattack-virtual
	sudo systemctl start rackattack-virtual

uninstall:
	-sudo systemctl stop rackattack-virtual
	-sudo systemctl disable rackattack-virtual
	-sudo rm -fr /usr/lib/systemd/system/rackattack-virtual.service
	sudo rm -fr /usr/share/rackattack.virtual
