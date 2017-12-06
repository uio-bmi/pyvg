from setuptools import setup

setup(name='pyvg',
      version='1.0.0',
      description='Working with vg graphs in python',
      url='http://github.com/uio-bmi/pyvg',
      author='Ivar Grytten and Knut Rand',
      author_email='',
      license='MIT',
      packages=['pyvg'],
      zip_safe=False,
      install_requires=['numpy', 'filecache', 'protobuf3', 'pystream-protobuf'],
      classifiers=[
            'Programming Language :: Python :: 3'
      ]

      )
