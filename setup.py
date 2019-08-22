import setuptools

setuptools.setup(
    name='twofa',
    version='0.23',
    description='A simple command-line 2-factor authentication token manager',
    author='Nils Werner, pepa65',
    author_email='pepa65@passchier.net',
    licence='GPLv3+',
    long_description='',
    url='https://github.com/pepa65/twofa',
    entry_points={'console_scripts': ['twofa = twofa.__init__:cli']},
    install_requires=[
        'pyqrcode',
        'pyotp',
        'click',
        'pyyaml',
        'cryptography',
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        'Environment :: Console',
        'Topic :: Security',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ]
)
