import shlex
from subprocess import run


def execute(command, url):
    cmd = shlex.split(command)
    cmd.append(url)
    run(cmd)
