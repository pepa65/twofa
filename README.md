# twofa
**Version 0.23**

Manage two-factor authentication store

## Installation

    git clone https://gitlab.com/pepa65/twofa
    cd twofa
    python3 setup.py build
    sudo python3 setup.py install

## Usage

**Display all tokens**

    twofa [list]

**Display tokens whose labels match a regular expression**

    twofa list 'Regex'

**Add secret**

    twofa add 'Label name' 'Secret'

**Delete secret**

    twofa remove [--confirm] 'Label name'

**Rename label**

    twofa rename 'Label name' 'New name'

**Encrypt store**

    twofa password

You will be asked to enter a new password. If you leave this password empty, the data will be stored unencrypted.

**Display QR for secret**

    twofa qr 'Label name'

Better visibility with a light terminal theme:

    twofa qr [--invert|-i] 'Label name'

