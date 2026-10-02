SHELL := /bin/bash
VERSION := $(shell cat VERSION)
ARCH ?= amd64

.PHONY: all deps glass-deps package glass iso iso-glass iso-flybase test kernel clean lint checksum release-bundle apt-repo sbom

all: package iso

deps:
	sudo ./build/prepare-host.sh

glass-deps:
	sudo ./build/prepare-glass-host.sh

package:
	./build/build-package.sh

glass:
	./build/build-glass.sh

iso: package
	sudo ./build/build-iso.sh

iso-glass: package glass
	sudo ./build/build-iso.sh

iso-flybase: package
	sudo ./build/build-flybase-iso.sh

test:
	./build/test-qemu.sh

kernel:
	./kernel/build-flykernel.sh

clean:
	sudo ./build/clean.sh

lint:
	./tests/smoke.sh

checksum:
	cd dist && sha256sum FlyOS-$(VERSION)-$(ARCH).iso > FlyOS-$(VERSION)-$(ARCH).iso.sha256

release-bundle: package
	./build/release-bundle.sh

apt-repo: package
	./build/build-apt-repo.sh

sbom:
	./build/sbom.py
