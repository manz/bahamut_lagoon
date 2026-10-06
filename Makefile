V = 0
Q = $(if $(filter 1,$V),,@)
# V=1 also turns on build.py's progress logging (./build.py -vv dumps the rooms).
BUILD_FLAGS = $(if $(filter 1,$V),-v,)

M = $(shell if [ "$$(tput colors 2> /dev/null || echo 0)" -ge 8 ]; then printf "\033[34;1m▶\033[0m"; else printf "▶"; fi)

# Prefer the checkout's venv (`uv sync` creates it), fall back to whatever
# is on PATH.
PY ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

ROM = build/bl.sfc
IPS = build/bl.ips
DEBUG_IPS = build/bl-debug.ips
# Only the tracked sources: the checkout also holds scratch asm (debug_src/,
# old experiments) that is neither built nor kept to the gate.
SOURCES = bl.s $(wildcard src/*.s src/*.i)
TEXTS = $(wildcard text/*.xml text/fr/*.xml text/fr/dialog/*.xml text/fr/battle/*.xml text/table/*.tbl)

# uv format fetches its own ruff: run the one pinned in the dev group.
RUFF_VERSION = $(shell uv run ruff --version | cut -d' ' -f2)
UV_FORMAT = uv format --preview-features format-command --version $(RUFF_VERSION)

.SUFFIXES:
.PHONY: all
all: | build tests  ## Build the patch and run the tests

.PHONY: build
build: $(IPS)  ## Assemble the IPS patch

# The base ROM is deliberately not a prerequisite: as a rule it would be
# something `make -B` tries to remake, and it is an input we can only ask
# the user to provide. CI decrypts bl.sfc.gz.gpg into place with a
# secret passphrase.
$(IPS): $(SOURCES) $(TEXTS) fonts/fft.png fonts/8x8vwf.png katsuji.toml build.py
	$(Q) test -s $(ROM) || { \
		echo "$(ROM) missing. Place an unheadered Bahamut Lagoon (J) ROM there."; \
		exit 1; }
	$(info $(M) Building patch...)
	$(Q) $(PY) ./build.py $(BUILD_FLAGS)
	$(Q) test -s $(IPS)

.PHONY: debug
debug: $(DEBUG_IPS)  ## Assemble the patch with the game's debug mode on

$(DEBUG_IPS): $(IPS)
	$(info $(M) Building debug patch...)
	$(Q) $(PY) ./build.py --debug $(BUILD_FLAGS)
	$(Q) test -s $(DEBUG_IPS)

.PHONY: tests
tests: $(IPS) $(DEBUG_IPS)  ## Run the full suite against freshly built patches
	$(info $(M) Running tests...)
	$(Q) $(PY) -m pytest

.PHONY: test
test: tests  ## Alias for `tests`

.PHONY: check
check:  ## Verify formatting and run the a816 fluff and ruff lints
	$(info $(M) Checking sources...)
	$(Q) uv run a816 format --check $(SOURCES)
	$(Q) uv run a816 check $(SOURCES)
	$(Q) $(UV_FORMAT) --check
	$(Q) uv run ruff check

.PHONY: format
format:  ## Rewrite sources in a816 and ruff canonical form
	$(info $(M) Formatting sources...)
	$(Q) uv run a816 format $(SOURCES)
	$(Q) $(UV_FORMAT)
	$(Q) uv run ruff check --fix

.PHONY: clean
clean:  ## Remove build products, keeping the base ROM
	$(info $(M) cleaning ...)
	$(Q) rm -f build/bl*.ips build/bl*.sym build/rooms.partial assets/vwf.bin assets/small_font.dat
	$(Q) rm -rf build/obj __pycache__ .pytest_cache

.PHONY: help
help: ## Display help
	@grep -hE '^[ a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-17s\033[0m %s\n", $$1, $$2}'
