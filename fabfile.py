from fabric.api import local
from celery.task import control

def clean():
    local('find . -name "*.pyc" -exec rm -rf {} \;')

def lint():
    local('find . -name "*.py" ! -name "fabfile.py" | xargs pylint | tee pylint.log | less')

def celery_tasks():
    inspector = control.inspect()
    registered = inspector.registered()
    for vhost in registered:
        print("{}:".format(vhost))
        for task in registered[vhost]:
            print("\t{}".format(task))
