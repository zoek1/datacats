from __future__ import absolute_import

from os import environ
import json
from urlparse import urlparse

from docker import Client
from docker.utils import kwargs_from_env
from docker.errors import APIError

_docker_kwargs = kwargs_from_env()
_docker = Client(**_docker_kwargs)

class WebCommandError(Exception):
    def __str__(self):
        return ('Command failed: {0}\n View command output:'
            ' docker logs {1}'.format(*self.args))

_boot2docker = None
def is_boot2docker():
    global _boot2docker
    if _boot2docker is None:
        _boot2docker = 'Boot2Docker' in _docker.info()['OperatingSystem']
    return _boot2docker

def docker_host():
    url = _docker_kwargs.get('base_url')
    if not url:
        return 'localhost'
    return urlparse(url).netloc.split(':')[0]


def ro_rw_to_binds(ro, rw):
    """
    ro and rw {localdir: binddir} dicts to docker-py's
    {localdir: {'bind': binddir, 'ro': T/F}} binds dicts
    """
    out = {}
    if ro:
        for localdir, binddir in ro.iteritems():
            out[localdir] = {'bind': binddir, 'ro': True}
    if rw:
        for localdir, binddir in rw.iteritems():
            out[localdir] = {'bind': binddir, 'ro': False}
    return out

def binds_to_volumes(volumes):
    """
    Return the target 'bind' dirs of volumnes from a volumes dict
    for passing to create_container
    """
    return [v['bind'] for v in volumes.itervalues()]

def web_command(command, ro=None, rw=None, links=None,
        image='datacats/web'):
    """
    Run a single command in a web image optionally preloaded with the ckan
    source and virtual envrionment.

    :param command: command to execute
    :param ro: {localdir: binddir} dict for read-only volumes
    :param rw: {localdir: binddir} dict for read-write volumes
    :param links: links passed to start
    :param image: docker image name to use
    """
    binds = ro_rw_to_binds(ro, rw)
    c = _docker.create_container(
        image=image,
        command=command,
        volumes=binds_to_volumes(binds),
        detach=False)
    _docker.start(
        container=c['Id'],
        links=links,
        binds=binds)
    if _docker.wait(c['Id']):
        raise WebCommandError(command, c['Id'][:12])
    _docker.remove_container(container=c['Id'])

def run_container(name, image, command=None, environment=None,
        ro=None, rw=None, links=None, detach=True, volumes_from=None,
        port_bindings=None):
    """
    simple wrapper for docker create_container, start calls

    :returns: container info dict or None if container couldn't be created
    """
    binds = ro_rw_to_binds(ro, rw)
    try:
        c = _docker.create_container(
            name=name,
            image=image,
            command=command,
            environment=environment,
            volumes=binds_to_volumes(binds),
            detach=detach,
            ports=list(port_bindings) if port_bindings else None)
    except APIError as e:
        return None
    _docker.start(
        container=c['Id'],
        links=links,
        binds=binds,
        volumes_from=volumes_from,
        port_bindings=port_bindings)
    return c

def remove_container(name, force=False):
    """
    Wrapper for docker remove_container

    :returns: True if container was found and removed
    """

    try:
        if not force:
            _docker.stop(name)
    except APIError as e:
        pass
    try:
        _docker.remove_container(name, force=True)
        return True
    except APIError as e:
        return False

def inspect_container(name):
    """
    Wrapper for docker inspect_container

    :returns: container info dict or None if not found
    """
    try:
        return _docker.inspect_container(name)
    except APIError as e:
        return None

def pull_stream(image):
    """
    Return generator of pull status objects
    """
    return (json.loads(s) for s in _docker.pull(image, stream=True))

def data_only_container(name, volumes):
    """
    create "data-only container" if it doesn't already exist.

    We'd like to avoid these, but postgres + boot2docker make
    it difficult, see issue #5
    """
    info = inspect_container(name)
    if info:
        return
    c = _docker.create_container(
        name=name,
        image='scratch', # minimal container
        command='true',
        volumes=volumes,
        detach=True)
    return c