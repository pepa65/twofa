# twofa
**Version 0.23**

A command-line 2-factor authentication manager.


## Installation

    pip install twofa


## Usage

**Print Token**

    twofa

**Add secret**

    twofa add 'Service Name' 'Secret'

**Delete secret**

    twofa rm --confirm 'Service Name'

**Rename Service**

    twofa rename 'Service Name' 'New Name'

**Encrypt store**

    twofa passwd

You will be asked to enter a new password. If you leave this password empty,
the data will be stored unencrypted.

**Print QR code**

    twofa qr 'Service Name'

if you are using a light terminal theme:

    twofa qr --invert 'Service Name'


### Bash autocomplete

We are using [Click bash integration](http://click.pocoo.org/5/bashcomplete/), which means you only need to add

    eval "$(_2FA_COMPLETE=source twofa)"

to your `~/.bashrc` to get autocompletion.
