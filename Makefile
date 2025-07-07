
.PHONY: docker-build build/venv docker-run docker-clean clean


build/venv:
	mkdir build && python -m venv build/venv && . build/venv/bin/activate && \
      poetry install --without dev


docker-build:
	docker build -t galileo-callback:latest .


docker-run:
	docker run --name galileo-callback -p 8080:8080 galileo-callback:latest

docker-clean:
	docker rm -f galileo-callback

clean:
	rm -rf build


