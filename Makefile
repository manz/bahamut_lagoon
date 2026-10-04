VERSION ?= 0.0.0.dev0
V = 0
Q = $(if $(filter 1,$V),,@)

M = $(shell if [ "$$(tput colors 2> /dev/null || echo 0)" -ge 8 ]; then printf "\033[34;1m▶\033[0m"; else printf "▶"; fi)

export VERSION

.SUFFIXES:
.PHONY: all
all: | bl.ips  ## Builds everything

.PHONY: format
format: ## Runs black to format the python code
	$(Q) hatch run tests:format

.PHONY: tests
tests: ## Runs unit tests
	$(Q) hatch run tests:tests

.PHONY: clean
clean: ## Cleanup everything
	$(info $(M) cleaning ...)
	rm -f rooms.partial bl.ips
	rm -f assets/vwf.bin

bl.ips: assets/vwf.bin rooms.partial ## Build IPS patch
	./build.py

rooms.partial: $(wildcard text/battle/*.xml) $(wildcard text/dialog/*.xml) ## Builds the rooms assets
	./build.py --rooms

assets/vwf.bin: $(wildcard fonts/vwf*.png) ## Builds the font asset
	mkdir -p assets
	python ./utils/font.py


.PHONY: env
env: ## Builds development virtualenv
	$(Q) hatch env remove tests
	$(Q) hatch env create tests

.PHONY: help
help: ## Display help
	@grep -hE '^[ a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-17s\033[0m %s\n", $$1, $$2}'
