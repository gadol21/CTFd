from __future__ import print_function

from CTFd.utils.user import is_admin
from CTFd.utils.decorators import admins_only
from CTFd.cache import cache
from CTFd.models import db
from .models import Containers

import json
import subprocess
import socket
import tempfile
import shutil
import re
import os
import sys


@cache.memoize()
def can_create_container():
    try:
        subprocess.check_output(['docker', 'version'])
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def import_image(name):
    try:
        info = json.loads(subprocess.check_output(['docker', 'inspect', '--type=image', name]))
        container = Containers(name=name, buildfile=None)
        db.session.add(container)
        db.session.commit()
        db.session.close()
        return True
    except subprocess.CalledProcessError:
        return False


def get_challenge_dir(challenge_name):
    return os.path.join('/opt/CTFd/challenges', challenge_name)


def create_image(name, add_to_db=True):
    if not can_create_container():
        return False

    # repository name component must match "[a-z0-9](?:-*[a-z0-9])*(?:[._][a-z0-9](?:-*[a-z0-9])*)*"
    # docker build -f /opt/CTFd/name -t name
    try:
        cmd = ['docker', 'build', '-t', name, get_challenge_dir(name)]
        print(cmd, file=sys.stderr)
        subprocess.call(cmd)
        if add_to_db:
            container = Containers(name)
            db.session.add(container)
            db.session.commit()
            db.session.close()
        return True
    except subprocess.CalledProcessError:
        return False


def is_port_free(port):
    s = socket.socket()
    result = s.connect_ex(('127.0.0.1', port))
    if result == 0:
        s.close()
        return False
    return True


def delete_image(name):
    try:
        subprocess.call(['docker', 'rm', '-f', name])
        #subprocess.call(['docker', 'rmi', '-f', name])
        return True
    except subprocess.CalledProcessError:
        return False


def run_image(name):
    try:
        info = json.loads(subprocess.check_output(['docker', 'inspect', '--type=image', name]))

        try:
            ports_asked = info[0]['Config']['ExposedPorts'].keys()
            ports_asked = [int(re.sub('[A-Za-z/]+', '', port)) for port in ports_asked]
        except KeyError:
            ports_asked = []

        cmd = ['docker', 'run', '-d', '-v', '{0}:/root/challenge:ro'.format(get_challenge_dir(name))]
        ports_used = []
        for port in ports_asked:
            if is_port_free(port):
                cmd.append('-p')
                cmd.append('{}:{}'.format(port, port))
            else:
                cmd.append('-p')
                ports_used.append('{}'.format(port))
        cmd += ['--name', name, name]
        print(cmd, file=sys.stderr)
        subprocess.call(cmd)
        return True
    except subprocess.CalledProcessError:
        return False


def container_start(name):
    try:
        cmd = ['docker', 'start', name]
        subprocess.call(cmd)
        return True
    except subprocess.CalledProcessError:
        return False


def container_stop(name):
    try:
        cmd = ['docker', 'stop', '-t', '1',  name]
        subprocess.call(cmd)
        return True
    except subprocess.CalledProcessError:
        return False


def container_status(name):
    try:
        data = json.loads(subprocess.check_output(['docker', 'inspect', '--type=container', name]))
        status = data[0]["State"]["Status"]
        return status
    except subprocess.CalledProcessError:
        return 'missing'



def container_ports(name, verbose=False):
    try:
        info = json.loads(subprocess.check_output(['docker', 'inspect', '--type=container', name]))
        if verbose:
            ports = info[0]["NetworkSettings"]["Ports"]
            if not ports:
                return []
            final = []
            for port in ports.keys():
                final.append("".join([ports[port][0]["HostPort"], '->', port]))
            return final
        else:
            ports = info[0]['Config']['ExposedPorts'].keys()
            if not ports:
                return []
            ports = [int(re.sub('[A-Za-z/]+', '', port)) for port in ports]
            return ports
    except subprocess.CalledProcessError:
        return []