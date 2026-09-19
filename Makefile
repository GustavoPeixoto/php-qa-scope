SERVICES := dev php

.DEFAULT_GOAL := help

.PHONY: help env env-dev env-php

help:
	@printf '%s\n' 'Available targets:'
	@printf '  %-16s %s\n' 'make help' 'Show this help message.'
	@printf '  %-16s %s\n' 'make env' 'Create root and service .env files for every service.'
	@printf '  %-16s %s\n' 'make env-dev' 'Create root .env and docker/dev/.env files.'
	@printf '  %-16s %s\n' 'make env-php' 'Create root .env and docker/php/.env files.'

env:
	@./tools/env $(SERVICES)

env-dev:
	@./tools/env dev

env-php:
	@./tools/env php
