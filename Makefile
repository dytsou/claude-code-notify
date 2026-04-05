.PHONY: install uninstall test ci

install:
	chmod +x scripts/install.sh
	bash scripts/install.sh

uninstall:
	chmod +x scripts/uninstall.sh
	bash scripts/uninstall.sh

test:
	chmod +x scripts/test.sh
	bash scripts/test.sh

ci:
	python3 -m compileall -q src
	bash -n scripts/install.sh scripts/uninstall.sh scripts/test.sh
	PYTHONPATH=src python3 -m unittest discover -s tests -v
