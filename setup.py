from setuptools import setup

setup(
    name='necrophos-wsgi',
    version='0.0.1',
    description='wsgi-like server based on asyncio',
    author='Elephant Liu',
    author_email='lexdene@gmail.com',
    url='https://github.com/lexdene/necrophos-wsgi',
    license='GPLv3',
    packages=['necrophos_wsgi'],
    entry_points={
        'console_scripts': [
            'necrophos_wsgi = necrophos_wsgi.main:main'
        ]
    },
)
