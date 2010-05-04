from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='wiseguy',
    version=version,
    description="Some useful WSGI utils for dealing with Werkzeug and Jinja",
    long_description="""\
""",
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Ed Singleton',
    author_email='singletoned@gmail.com',
    url='http://singletoned.net',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Werkzeug>=0.6",
        "Jinja2>=2.4",
        "pesto>=16",
        "lxml",
    ],
    entry_points="""
      # -*- Entry points: -*-
      """,
)
