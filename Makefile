.DEFAULT_GOAL := all
.PHONY: up
up:
	mv hs_data_services/hs_data_services/local_settings.py hs_data_services/hs_data_services/local_settings.py.bak.$(shell date +%s) || true
	cp hs_data_services/hs_data_services/local_settings.local hs_data_services/hs_data_services/local_settings.py
	docker-compose -f local-dev.yml up -d --build

.PHONY: down
down:
	docker-compose -f local-dev.yml down