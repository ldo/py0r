#+
# Setuptools script to install py0r. Make sure setuptools
# <https://setuptools.pypa.io/en/latest/index.html> is installed.
# Invoke from the command line in this directory as follows:
#
#     python3 setup.py build
#     sudo python3 setup.py install
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import setuptools

setuptools.setup \
  (
    name = "py0r",
    version = "0.8",
    description = "language bindings for the Frei0r effects plugins, for Python 3.4 or later",
    author = "Lawrence D'Oliveiro",
    author_email = "ldo@geek-central.gen.nz",
    url = "https://github.com/ldo/py0r",
    py_modules = ["f0r"],
  )
