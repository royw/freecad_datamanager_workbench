"""Setuptools packaging configuration for the workbench Python package.

 This is used for packaging/installing `freecad.datamanager_wb`.
 """

from setuptools import setup
import os

version_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "freecad", "datamanager_wb", "version.py")
with open(version_path) as fp:
    __version__ = "0.0.0"
    exec(fp.read())

setup(name='freecad.datamanager_wb',
      version=str(__version__),
      packages=['freecad',
                'freecad.datamanager_wb'],
      maintainer="Roy Wright",
      maintainer_email="roy@wright.org",
      url="https://github.com/royw/freecad_datamanager_workbench",
      description="Manages FreeCAD varsets and aliases",
      install_requires=['numpy',],
      include_package_data=True)
