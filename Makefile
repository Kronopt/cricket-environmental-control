install-requirements:
	python -m pip install -r requirements.txt

update:
	git clean -d -f -q
	git reset --hard
	git checkout main
	git pull origin main
	chmod +x run.sh setup.sh

restart:
	shutdown -r now

run:
	python main.py

run-debug:
	python main.py -l DEBUG
