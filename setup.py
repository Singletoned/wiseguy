from setuptools import setup, find_packages
import sys, os

version = '0.2.13'

setup(
    name='wiseguy',
    version=version,
    description="Some useful WSGI utils for dealing with Werkzeug and Jinja",
    long_description="""\
""",
    classifiers=[
        "Programming Language :: Python",
        "License :: Freely Distributable",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 4 - Beta",
    ],
    keywords='',
    author='Ed Singleton',
    author_email='singletoned@gmail.com',
    url='http://singletoned.net',
    license='',
    scripts=["wiseguy/scripts/parse_jade.py", "wiseguy/scripts/html2jade.py"],
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Werkzeug>=0.6",
        "Jinja2>=2.4",
        "lxml",
        "cssselect",
        "sqlalchemy>0.6",
    ],
    entry_points="""
      # -*- Entry points: -*-
      """,
)
