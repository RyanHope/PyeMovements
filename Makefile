VERSION := `git describe --tags --dirty`

help:
	@echo "Options: bundle"

bundle:
	rm -f bundle
	mkdir -p bundle/crisp/simpy/resources
	cp antisaccade.py crisp.py bundle/crisp
	cp simpy/*.py bundle/crisp/simpy
	cp simpy/resources/*.py bundle/crisp/simpy/resources
	cd bundle; zip -r crisp-$(VERSION).zip crisp

clean:
	rm -f `find *.zip *.pyc latencies*`
	rm -rf bundle
