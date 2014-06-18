all: test check_convention

clean:
	rm -fr build dist rackattack.egg-info images.fortests

test: unittest whiteboxtest
UNITTESTS=$(shell find rackattack -name 'test_*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
COVERED_FILES=rackattack/common/hoststatemachine.py,rackattack/common/hosts.py,rackattack/virtual/alloc/allocations.py,rackattack/virtual/alloc/allocation.py,rackattack/virtual/alloc/freepool.py
unittest:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. coverage run -m unittest $(UNITTESTS)
	coverage report --show-missing --rcfile=coverage.config --fail-under=100 --include=$(COVERED_FILES)

WHITEBOXTESTS=$(shell find tests -name 'test_*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
whiteboxtest:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. python -m unittest $(WHITEBOXTESTS)

testone:
	UPSETO_JOIN_PYTHON_NAMESPACES=Yes PYTHONPATH=. python tests/test$(NUMBER)_*.py

check_convention:
	pep8 rackattack --max-line-length=109

uninstall:
	sudo pip uninstall rackattack
	sudo rm /usr/bin/rackattack

install:
	-sudo pip uninstall rackattack
	python setup.py build
	python setup.py bdist
	sudo python setup.py install
	sudo cp rackattack.sh /usr/bin/rackattack
	sudo chmod 755 /usr/bin/rackattack
