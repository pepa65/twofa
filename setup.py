import setuptools

setuptools.setup(
    name='twofa',
    version='0.28',
    description='Manage a two-factor authentication store on the commandline',
    author='Nils Werner, pepa65',
    author_email='pepa65@passchier.net',
    license='GPLv3+',
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
