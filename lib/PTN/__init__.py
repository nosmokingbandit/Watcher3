#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .parse import PTN

__author__ = 'Divij Bindlish'
__email__ = 'dvjbndlsh93@gmail.com'
__version__ = '1.1.1'
__license__ = 'MIT'

ptn = PTN()


def parse(name):
    return ptn.parse(name)
