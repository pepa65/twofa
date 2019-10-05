# twofa
**Version 0.25**

Manage two-factor authentication store on the command-line

## Requirements
    dev
    setuptools
    cryptography

Either python2.7 or python3 work, install the corresponding packages first:
`python-dev python-setuptools python-cryptography` or
`python3-dev python3-setuptools python3-cryptography`.

## Installation
    git clone https://gitlab.com/pepa65/twofa
    cd twofa
    python setup.py build
    sudo python setup.py install

## Usage
**Display all tokens**

    twofa [show]

**Display tokens whose labels match regex pattern**

    twofa show 'Regex'

**Add secret to store**

    twofa add 'Label name' 'Secret'

**Remove secret**

    twofa remove [--confirm] 'Label name'

The --confirm option will force the removal.

**Rename the label of a secret in store**

    twofa rename 'Label name' 'New name'

**Set password**

    twofa password

You will be asked to enter a new password. If you leave this password empty, the data will be stored unencrypted.

**Display secret**

    twofa secret 'Label name'

**Display QR code for secret**

    twofa qr 'Label name'

Better visibility with a light terminal theme:

    twofa qr [--invert|-i] 'Label name'

