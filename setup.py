from __future__ import print_function

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

from glob import glob
import sys
import os
from pynfs import VERSION

DESCRIPTION = """
pynfs
============

Add stuff here.
"""

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()


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
        from pynfs.xdr import xdrgen
        xdr_files = glob(os.path.join(directory, "*.x"))
        for file in xdr_files:
            # Can conditionalize this
            # XXX need some way to pass options here
            print('running xdrgen on', file)
            xdrgen.run(file, output_directory=directory)


setup(name="pynfs",
      packages=find_packages(),
      version=VERSION,
      description="NFS tools, tests, and support libraries",
      long_description=DESCRIPTION,
      setup_requires=['setuptools>=17.1', 'ply'],
      install_requires=requirements,
      # cmdclass={"build_py": build_py, "install": CustomInstall},
      cmdclass={"build_py": CustomBuildPy},
      scripts=['pynfs/xdr/xdrgen.py'],

      # These will be the same
      author="Fred Isaman",
      author_email="iisaman@citi.umich.edu",
      maintainer="Fred Isaman",
      maintainer_email="iisaman@citi.umich.edu",
      url="http://www.citi.umich.edu/projects/nfsv4/pynfs/",
      license="GPL"
      )
