from setuptools import setup

setup(
    name='notetaker',
    version='0.1',
    py_modules=['notes'],
    include_package_data=True,
    install_requires=[
        'click'
    ],
    entry_points='''
        [console_scripts]
        notes=notes:cli
    ''',
)