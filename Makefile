.PHONY: install uninstall test ci

install:
	bash install.sh

uninstall:
	bash uninstall.sh

test:
	bash test.sh

ci:
	python3 -m compileall -q notify.py presummary.py
	bash -n install.sh uninstall.sh test.sh
	PYTHONPATH=. python3 -m unittest discover -s tests -v
