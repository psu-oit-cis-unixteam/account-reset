from fabric.api import local

def clean():
    local('find . -name "*.pyc" -exec rm -rf {} \;')

def lint():
    local('find . -name "*.py" ! -name "fabfile.py" | xargs pylint | tee pylint.log | less')
