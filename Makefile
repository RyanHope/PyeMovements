VERSION := `git describe --tags --dirty`
CRISP		:= crisp-$(VERSION)

help:
	@echo "Options: bundle"

bundle:
	rm -f bundle
	mkdir -p bundle/$(CRISP)/simpy/resources
	cp antisaccade.py crisp.py bundle/$(CRISP)
	cp latencies_pro.csv bundle/$(CRISP)
	cp latencies_anti.csv bundle/$(CRISP)
	cp amplitudes_pro.csv bundle/$(CRISP)
	cp amplitudes_anti.csv bundle/$(CRISP)
	cp simpy/*.py bundle/$(CRISP)/simpy
	cp simpy/resources/*.py bundle/$(CRISP)/simpy/resources
	cd bundle; zip -r $(CRISP).zip $(CRISP)

clean:
	rm -f `find *.zip *.pyc`
	rm -rf bundle
