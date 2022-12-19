#!/usr/bin/env python3

from __future__ import print_function

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.install import install

from glob import glob
import sys
import os
from pynfs.xdr import xdrgen

DESCRIPTION = """
pynfs
============

Add stuff here.
"""

# DIRS = ["xdr", "rpc", "nfs41", "nfs40"] # Order is important

class CustomBuildPy(build_py):  # used in setup.cfg
    """Specialized Python source builder that scans for .x files"""

    command_name = 'build_py'

    def build_packages(self):
        # A copy from _build_py, with a call to expand_xdr added
        for package in self.packages:
            package_dir = self.get_package_dir(package)
            CustomBuildPy.expand_xdr(package_dir)

        super().build_packages()

    @classmethod
    def expand_xdr(cls, directory):
        xdr_files = glob(os.path.join(directory, "*.x"))
        for file in xdr_files:
            # Can conditionalize this
            # XXX need some way to pass options here
            print('running xdrgen on', file)
            xdrgen.run(file, output_directory=directory)


setup(name="pynfs",
      packages=find_packages(),
      description="NFS tools, tests, and support libraries",
      long_description=DESCRIPTION,
      setup_requires=['pbr>=1.9', 'setuptools>=17.1'],
      pbr=True,
      # cmdclass={"build_py": build_py, "install": CustomInstall},
      cmdclass={"build_py": build_py},
      scripts=['pynfs/xdr/xdrgen.py', 'pynfs/nfs40/testserver.py', './showresults.py'],

      # These will be the same
      author="Fred Isaman",
      author_email="iisaman@citi.umich.edu",
      maintainer="Fred Isaman",
      maintainer_email="iisaman@citi.umich.edu",
      url="http://www.citi.umich.edu/projects/nfsv4/pynfs/",
      license="GPL"
      )
