from __future__ import print_function, absolute_import
import os
import sys
import time
import base64
import getpass
import binascii

import re
import click
import pyotp
import pyqrcode
import yaml
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def create_fernet(passwd, salt=None):
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=500000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(passwd.encode()))
    return Fernet(key), salt


def encrypt(data, passwd):
    f, salt = create_fernet(passwd)

    return f.encrypt(yaml.dump(data).encode()).decode(), base64.b64encode(salt)


def decrypt(data, passwd, salt):
    salt = base64.b64decode(salt)
    f, _ = create_fernet(passwd, salt)

    return yaml.load(f.decrypt(data.encode()))


class Store(object):
    encrypted = False
    passwd = None

    def load_secrets(self):
        try:
            with open(os.path.expanduser('~/.twofa.yaml'), 'r') as outfile:
                data = yaml.load(outfile)
            try:
                if data['encrypted']:
                    self.passwd = getpass.getpass("Enter store password: ")
                    self.encrypted = True
                    try:
                        data['secrets'] = decrypt(
                            data['secrets'], self.passwd, data['salt']
                        )
                    except InvalidToken:
                        raise click.ClickException("Invalid password")

                click.echo("OK\n")
                return data['secrets']
            except KeyError:
                return data
        except (yaml.YAMLError, IOError):
            return {}

    def save_secrets(self, secrets, passwd=None):
        salt = ""
        if passwd is not None:
            self.passwd = passwd
            self.encrypted = True

        if passwd == "":
            self.encrypted = False

        if self.encrypted:
            secrets, salt = encrypt(secrets, self.passwd)

        data = {
            'encrypted': self.encrypted,
            'salt': salt,
            'secrets': secrets
        }

        with open(os.path.expanduser('~/.twofa.yaml'), 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)


def totp(secret):
    return pyotp.TOTP(secret).now()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """ 2fa - Manage two-factor authentication store """
    if ctx.invoked_subcommand is None:
        return listcmd()


@cli.command(name='list')
@click.argument('pattern', default="")
def listcmd(pattern):
    """ List secrets that match regex pattern """
    store = Store()
    secrets = store.load_secrets()

    some = False
    for label, secret in secrets.items():
        #if pattern == "" or re.match(pattern+"$", label):
        if pattern == "" or re.search(pattern, label, re.IGNORECASE):
            click.echo("{}  {}".format(totp(secret), label))
            some = True

    if some:
        expire = 30-(int(time.time())%30)
        click.echo("\nExpiration in {} seconds".format(expire))
    else:
        click.echo("Nothing found matching pattern '{}'".format(pattern))


@cli.command(name='add')
@click.argument('label')
@click.argument('secret')
def addcmd(label, secret):
    """ Add secret to store """
    store = Store()
    secrets = store.load_secrets()

    if secrets.get(label):
        raise click.ClickException("Label '{}' already present, aborting".format(label))

    try:
        secret = "".join(secret.split())
        totp(secret)
        secrets[label] = secret
    except (TypeError, binascii.Error):
        raise click.ClickException("Invalid secret! Only A-Z and 2-7 allowed, and no spaces, aborting")

    store.save_secrets(secrets)
    click.echo("Secret stored with label '{}'".format(label))


@cli.command(name='rename')
@click.argument('label')
@click.argument('new_label')
def renamecmd(label, new_label):
    """ Rename secret in store """
    store = Store()
    secrets = store.load_secrets()

    try:
        secrets[new_label] = secrets[label]
        del secrets[label]
    except KeyError:
        raise click.ClickException("Label '{}' not present, aborting".format(label))

    store.save_secrets(secrets)
    click.echo("Label '{}' renamed to '{}'".format(label, new_label))


@cli.command(name='remove')
@click.argument('label')
@click.option('--confirm/--no-confirm', default=False)
def rmcmd(label, confirm):
    """ Remove secret: --confirm option required! """
    store = Store()
    secrets = store.load_secrets()

    try:
        if secrets[label]: pass
    except KeyError:
        raise click.ClickException("Label '{}' not present, aborting".format(label))

    if not confirm:
        raise click.ClickException("The --confirm option is required, aborting")

    try:
        del secrets[label]
    except KeyError:
        raise click.ClickException("Label '{}' not present, aborting".format(label))

    store.save_secrets(secrets)
    click.echo("Label '{}' removed with secret".format(label))


@cli.command(name='qr')
@click.argument('label')
@click.option('--invert/--no-invert', default=False)
def qrcmd(label, invert):
    """ Print QR code for secret """
    store = Store()
    secrets = store.load_secrets()
    secret = secrets.get(label)

    if secret:
        qr = pyqrcode.create(
            'otpauth://totp/{}?secret={}'.format(label, secret.upper())
        )
        if invert:
            click.echo(qr.terminal(
                module_color='black', background='white', quiet_zone=1
            ))
        else:
            click.echo(qr.terminal(quiet_zone=1))
    else:
        raise click.ClickException("Label '{}' not present".format(label))


@cli.command(name='password')
def passwdcmd():
    """ Set password: empty = no encryption! """
    store = Store()
    secrets = store.load_secrets()

    newpasswd = getpass.getpass("Enter new store password: ")
    confirmpasswd = getpass.getpass("Confirm new store password: ")

    if not newpasswd == confirmpasswd:
        raise click.ClickException("New store passwords not matching, aborting")

    store.save_secrets(secrets, newpasswd)
    click.echo("New password set")
