#!/usr/bin/env python
# * coding: utf8 *
'''
boost

Usage:
  boost analyze --workspace <workspace>
  boost stats --workspace <workspace>
  boost postprocess --target <target> --workspace <workspace>
  boost -h | --help
  boost --version

Options:
  --target                          The target folder
  --workspace                       A geodatabse
  -h --help                         Show this screen.
  --version                         Show version.

Examples:
  boost analyze --workspace c:\bbservice_s12.gdb

Help:
  For help using this tool, please open an issue on the Github repository:
  https://github.com/agrc/broadband-cli
'''

from . import __version__ as VERSION
from docopt import docopt
from inspect import getmembers, isclass


def main():
    '''Main CLI entrypoint.
    '''
    import boost.commands
    options = docopt(__doc__, version=VERSION)

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.
    for k, v in options.items():
        if k[0] in ['-', '<', '['] or not v or not hasattr(boost.commands, k):
            continue

        module = getattr(boost.commands, k)
        boost.commands = getmembers(module, isclass)
        Command = [command[1] for command in boost.commands if command[0] != 'Command'][0]
        command = Command(options)
        command.execute()
