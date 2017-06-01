#!/usr/bin/env python
# * coding: utf8 *
'''
command.py

A module that contains the implementation of the command pattern
'''


class Command(object):
    '''An abstract command class.
    '''

    def __init__(self, options, *args, **kwargs):
        self.options = options
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        raise NotImplementedError('You must implement the execute() method in the inheriting class.')
