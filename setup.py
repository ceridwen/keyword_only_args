from setuptools import setup

setup(
    name = 'keyword_only_args',
    packages = ['keyword_only_args'],
    version = '1.0',
    description = 'A decorator to use keyword-only arguments in Python 2 and 3.',
    author = 'Ceridwen',
    author_email = 'ceridwenv@gmail.com',
    license = 'MIT',
    url = 'https://github.com/ceridwen/keyword_only_args',
    download_url = 'https://github.com/ceridwen/keyword_only_args/tarball/1.0',
    keywords = ['arguments', 'decorator', 'keyword', 'keyword_only'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development',
    ],
    install_requires = ['wrapt'],
    tests_require=['hypothesis']
)
