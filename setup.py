from setuptools import setup, find_packages
import sys, os
import vogelerserver

version = vogelerserver.__version__

setup(name='vogelerserver',
      version=version,
      description="Python-based Configuration Management Framework",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='cmdb management configuration',
      author='Luc Stepniewski',
      author_email='luc.stepniewski@adelux.fr',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
#      package_data = {
#          'vogelerserverdata': ['data/*',],
#      },
      tests_require='nose',
      test_suite='nose.collector',

      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'couchdbkit',
          'simplejson',
          'pyyaml',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      vogelerserver = vogelerserver.command:main
      """,
      )
