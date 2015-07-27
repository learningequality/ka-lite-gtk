"""
CLI for kalite
"""

from __future__ import print_function
from __future__ import unicode_literals

import getpass
import logging
import os
import re
import json
import pwd
import shlex
import subprocess

from distutils.spawn import find_executable

from .exceptions import ValidationError
from . import validators

logger = logging.getLogger(__name__)

KALITE_GTK_SETTINGS_FILE = os.path.expanduser(os.path.join('~', '.kalite', 'ka-lite-gtk.json'))

DEFAULT_USER = getpass.getuser()
DEFAULT_PORT = 8008

# A validator callback will raise an exception ValidationError
validate = {
    'user': validators.username,
    'port': validators.port
}

# Constants from the ka-lite .deb package conventions
DEBIAN_INIT_SCRIPT = '/etc/init.d/ka-lite'
DEBIAN_USERNAME_FILE = '/etc/ka-lite/username'
DEBIAN_OPTIONS_FILE = '/etc/ka-lite/server_options'

if find_executable('pkexec'):
    SU_COMMAND = 'pkexec --user {username}'
    SUDO_COMMAND = 'pkexec'
else:
    SU_COMMAND = 'gksudo -u {username}'
    SUDO_COMMAND = 'gksudo'

# KA Lite Debian convention
# Set new default values from debian system files
if os.path.isfile(DEBIAN_USERNAME_FILE):
    debian_username = open(DEBIAN_USERNAME_FILE, 'r').read()
    debian_username = debian_username.split('\n')[0]
    if debian_username:
        try:
            debian_username = validate['user'](debian_username)
            DEFAULT_USER = debian_username
            # Okay there's a default debian user. If that user is the same as
            # the one selected in the user settings, we should use the --port
            # option set for the debian service.
            if os.path.isfile(DEBIAN_OPTIONS_FILE):
                debian_options = open(DEBIAN_OPTIONS_FILE, 'r').read()
                port = re.compile(r'--port\s+(\d+)').search(debian_options)
                port = validate['port'](port, none_if_invalid=True)
                DEFAULT_PORT = port.group(1) if port else DEFAULT_PORT
        except ValidationError:
            logger.error('Non-existing username in {}'.format(DEBIAN_USERNAME_FILE))


def get_kalite_home(user):
    return os.path.join(pwd.getpwnam(user).pw_dir, '.kalite')


DEFAULT_HOME = get_kalite_home(DEFAULT_USER)


# These are the settings. They are subject to change at load time by
# reading in settings files
settings = {
    'user': DEFAULT_USER,
    'command': find_executable('kalite'),
    'content_root': os.path.join(DEFAULT_HOME, 'content'),
    'port': DEFAULT_PORT,
    'home': DEFAULT_HOME,
}


# Read settings from settings file
if os.path.isfile(KALITE_GTK_SETTINGS_FILE):
    try:
        loaded_settings = json.load(open(KALITE_GTK_SETTINGS_FILE, 'r'))
        for (k, v) in loaded_settings.items():
            try:
                settings[k] = validate[k](v) if k in validate else v
            except ValidationError:
                logger.error("Illegal value in {} for {}".format(KALITE_GTK_SETTINGS_FILE, k))
        # Update the home folder if it wasn't specified
        if 'home' not in loaded_settings:
            settings['home'] = get_kalite_home(settings['user'])
        if 'content_root' not in loaded_settings:
            print("SETTING CONTENT_ROOT")
            settings['content_root'] = os.path.join(settings['home'], 'content')
    except ValueError:
        logger.error("Parsing error in {}".format(KALITE_GTK_SETTINGS_FILE))


def get_command(kalite_command):
    return [settings['command']] + kalite_command.split(" ")


def conditional_sudo(cmd, no_su=False):
    """Decorator indicating that sudo access is needed before running
    run_kalite_command or stream_kalite_command"""
    if settings['user'] != getpass.getuser():
        return shlex.split(SU_COMMAND.format(username=settings['user'])) + cmd
    return cmd


def sudo(cmd, no_su=False):
    """Decorator indicating that sudo access is needed before running
    run_kalite_command or stream_kalite_command"""
    return shlex.split(SUDO_COMMAND) + cmd


def run_kalite_command(cmd, shell=False):
    """
    Blocking:
    Uses the current UI settings to run a command and returns
    stdin, stdout

    Example:

    run_kalite_command("start --port=7007")
    """
    env = os.environ.copy()
    env['KALITE_HOME'] = settings['home']
    logger.debug("Running command: {}, KALITE_HOME={}".format(cmd, str(settings['home'])))
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=shell
    )
    # decode() necessary to convert streams from byte to str
    return list(map(lambda x: x.decode(), p.communicate())) + [p.returncode]


def stream_kalite_command(cmd, shell=False):
    """
    Generator that yields for every line of stdout

    Finally, returns stderr

    Example:

    for stdout, stderr in stream_kalite_command("start --port=7007"):
        print(stdout)
    print(stderr)

    """
    env = os.environ.copy()
    env['KALITE_HOME'] = settings['home']
    logger.debug("Streaming command: {}, KALITE_HOME={}".format(cmd, str(settings['home'])))
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=shell
    )
    for line in iter(lambda: p.stdout.readline().decode(), ''):
        yield line, None, None
    yield (
        None,
        p.stderr.read().decode() if p.stderr is not None else None,
        p.returncode
    )


def has_init_d():
    return os.path.isfile(DEBIAN_INIT_SCRIPT)


def is_installed():
    return any('ka-lite' in x for x in os.listdir('/etc/rc3.d'))


def install():
    return run_kalite_command(
        sudo([
            "bash".encode('ascii'),
            "-c".encode('ascii'),
            "echo {username} > /etc/ka-lite/username && update-rc.d ka-lite defaults".format(username=settings['user']).encode('ascii')
        ])
    )


def remove():
    return run_kalite_command(
        sudo(shlex.split("update-rc.d -f ka-lite remove"))
    )


def start():
    """
    Streaming:
    Starts the server
    """
    for val in stream_kalite_command(conditional_sudo(get_command('start'))):
        yield val


def stop():
    """
    Streaming:
    Stops the server
    """
    for val in stream_kalite_command(conditional_sudo(get_command('stop'))):
        yield val


def diagnose():
    """
    Blocking:
    Runs the diagnose command
    """
    return run_kalite_command(get_command('diagnose'))


def status():
    """
    Blocking:
    Fetches server's current status as a string
    """
    __, err, __ = run_kalite_command(get_command('status'))
    return err


def save_settings():
    # Write settings to ka-lite-gtk settings file
    json.dump(settings, open(KALITE_GTK_SETTINGS_FILE, 'w'))

    # Write to debian settings if applicable
    pass
