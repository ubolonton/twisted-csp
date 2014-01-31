# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name="twisted-csp",
      version="0.1.4",
      description="Go-style channels for Twisted",
      author="Nguyễn Tuấn Anh",
      author_email="ubolonton@gmail.com",
      url="https://github.com/ubolonton/twisted-csp",
      long_description=open('README.md').read(),
      license="EPL",

      packages=find_packages("."),

      install_requires=[
          "twisted"
      ]
)
