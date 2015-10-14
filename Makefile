VERSION := `git describe --tags --dirty`

help:
	@echo "Options: bundle"

bundle:
	rm -f CRISP-$(VERSION).zip
	zip CRISP-$(VERSION).zip antisaccade.py crisp.py simpy/*.py simpy/resources/*.py

clean:
	rm -f `find *.zip *.pyc latencies*`
