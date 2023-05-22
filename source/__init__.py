from sys import argv
from sys import path as syspath
from os import path as ospath

syspath.append(ospath.join(ospath.dirname(__file__), '..', 'source'))

mock = False
if '--mock' in argv:
    mock = True

import source

