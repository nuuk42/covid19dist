# Makefile for covid19 Project
#
# Script to setup the runtime environment
ENV_DEV = source ./runtime/bin/activate
ENV_CLOUD = . ./bin/cloud_env
ENV_TEST = export PYTHONPATH=`pwd`/py
#
APP_NAME = covid19

# commandline overrides
tt = *
ff = 

# ----------------------------------------------------------------------------
#  Help
#
.PHONY: help
help:
	@echo "Help"	
	@echo ""
	@echo "Manage the COVID19 application."
	@echo ""
	@echo "Commands starting with cf_ are running towards the Pivotal CLOUD - other command are local."
	@echo "Commands starting with g_ are running towards the Google CLOUD - other command are local."
	@echo ""
	@echo "Cloud Commands:"
	@echo "cf_login   - login for CLOUD"
	@echo "cf_app     - show status of the application"
	@echo "cf_push    - deploy a new version"
	@echo "cf_start   - start the application"
	@echo "cf_stop    - stop the application"
	@echo "cf_logs    - tail the application log"
	@echo "cf_env     - show application environment"
	@echo "cf_ssh     - login for cloud container"
	@echo "cf_restage - restage the application using new configration parameters"
	@echo ""
	@echo "g_login    - init the google SDK"
	@echo "g_deploy   - deploy a new version"
	@echo "g_logs     - tail application logs"
	@echo "g_app      - show status of the application"
	@echo ""
	@echo "Local Commands:"
	@echo "run_flask    - run local using flak's internal WEB server"
	@echo "run_gunicorn - run local using gunicorn WEB server"
	@echo "env          - show local environment"
	@echo "runtime      - build a new python runtime"
	@echo "clean        - remove python runtime an all *.pyc files"
	
# ----------------------------------------------------------------------------
.PHONY: clean
clean:
	@-cd py; find -name *.pyc | xargs rm
	@-rm -Rf runtime

# Build the file py/requirements.txt
.PHONY: requirements.txt
requirements.txt:
	$(ENV_DEV); cd py; pip freeze > requirements.txt

# -----------------------------------------------------------------
# Running local

# run local using the internal flask WEB server
.PHONY: run_flask
run_flask: runtime
	$(ENV_DEV); $(ENV_CLOUD); cd py;python covid19_main.py	

# run local using gunicorn
.PHONY: run_gunicorn
run_gunicorn: runtime
	$(ENV_DEV); $(ENV_CLOUD); cd py;gunicorn -b 0.0.0.0:9099 --workers 5 --max-requests 1000 covid19_main

# show local environment
.PHONY: env
env:
	cat $(ENV_CLOUD)	
	

# build the python runtime
runtime:
	echo "building new python virtual env..."
	python3 -m venv runtime --prompt covid19
	echo "Done!"
	echo "updating pip..."
	$(ENV_DEV); pip install --upgrade pip
	echo "Done!"
	echo "installing dependencies..."
	$(ENV_DEV); pip install -r ./py/requirements.txt

# ==================================================
# = Pivotal CLOUD
# ==================================================

.PHONY: cf_push
cf_push: clean requirements.txt
	cd py; cf push	

# Show app status
.PHONY: cf_app
cf_app:
	cf app $(APP_NAME)	

# Show application logs
.PHONY: cf_logs
cf_logs:
	cf logs $(APP_NAME)	

# start the app
.PHONY: cf_start
cf_start:
	cf start $(APP_NAME)	

# stop the app
.PHONY: cf_stop
cf_stop:
	cf stop $(APP_NAME)	
	
# show environment
.PHONY: cf_env
cf_env:
	cf env $(APP_NAME)	

# connect to container using ssh
.PHONY: cf_ssh
cf_ssh:
	cf ssh $(APP_NAME)	

# re-stage with new parameters
.PHONY: cf_restage
cf_restage:
	cd py; cf restage $(APP_NAME)	

# login
.PHONY: cf_login
cf_login:
	echo "EMAIL=robert.k..."
	echo "Password=T..."
	cf login https://api.run.pivotal.io	

# ==================================================
# = GOOGLE CLOUD
# ==================================================

# login
.PHONY: g_login
g_login:
	@echo "Account: nuukzweiundvierzig@gmail.com"
	@echo ""
	gcloud init --project=braided-visitor-274714 --account=nuukzweiundvierzig@gmail.com --configuration=kl1 --console-only --skip-diagnostics

# deploy
.PHONY: g_deploy
g_deploy: clean
	cd py; gcloud app deploy --quiet

# tail logs
.PHONY: g_logs
g_logs:
	cd py; gcloud app logs tail	

# show application status
.PHONY: g_app
g_app:
	cd py; gcloud app describe

