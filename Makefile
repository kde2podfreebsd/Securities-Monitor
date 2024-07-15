clean:
	find . -name __pycache__ -type d -print0|xargs -0 rm -r --
	rm -rf .idea/

fix_git_cache:
	git rm -rf --cached .
	git add .

.PHONY: clean fix_git_cache

docker_build:
	docker build -t algopack_monitor .

docker_run:
	docker run -it algopack_monitor

.PHONY: docker_build docker_run

docker_clean:
	sudo docker stop $$(sudo docker ps -a -q) || true
	sudo docker rm $$(sudo docker ps -a -q) || true

pre_commit:
	pre-commit run flake8 --all-files