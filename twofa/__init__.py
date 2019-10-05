from __future__ import print_function, absolute_import
import os
import time
import base64
import getpass
import re
import click
import binascii
import pyotp
import pyqrcode
import yaml
import subprocess
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

version = '0.26'
configfile = '~/.twofa.yaml'

def create_fernet(passwd, salt=None):
	if salt is None:
		salt = os.urandom(16)
	kdf = PBKDF2HMAC(
		algorithm=hashes.SHA256(),
		length=32,
		salt=salt,
		iterations=777777,
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
	return yaml.load(f.decrypt(data.encode()), Loader=yaml.SafeLoader)

class Store(object):
	encrypted = False
	passwd = None
	def load_secrets(self):
		try:
			with open(os.path.expanduser(configfile), 'r') as outfile:
				data = yaml.load(outfile, Loader=yaml.SafeLoader)
			try:
				if data['encrypted']:
					self.passwd = getpass.getpass("Enter store password: ")
					self.encrypted = True
					try:
						data['secrets'] = decrypt(data['secrets'], self.passwd, data['salt'])
					except InvalidToken:
						raise click.ClickException("invalid password")
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
		with open(os.path.expanduser(configfile), 'w') as outfile:
			yaml.dump(data, outfile, default_flow_style=False)

def totp(secret):
	return pyotp.TOTP(secret).now()

@click.version_option(version=version)
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
	"""twofa - Manage a two-factor authentication store on the commandline"""
	if ctx.invoked_subcommand is None:
		return showcmd()

@cli.command(name='show')
@click.argument('pattern', default="")
def showcmd(pattern):
	"""Display tokens whose labels match regex pattern"""
	store = Store()
	secrets = store.load_secrets()
	list = ""
	expire = 30-(int(time.time())%30)
	for label, secret in secrets.items():
		if pattern == "" or re.search(pattern, label, re.IGNORECASE):
			list += "\n{}    {:2d} s    {}".format(totp(secret), expire, label)
	if list != "":
		header = " Token   Expire    Label".format(expire)
		click.echo_via_pager(header+list)
		click.pause("Press a key to clear the screen")
		subprocess.call(['tput', 'reset'])
	else:
		click.echo("No match for '{}'".format(pattern))

@cli.command(name='add')
@click.argument('label')
def addcmd(label):
	"""Add secret to store"""
	store = Store()
	secrets = store.load_secrets()
	if secrets.get(label):
		raise click.ClickException("label '{}' already exists".format(label))
	else:
		while True:
			secret = input("Enter secret (only A-Z and 2-7 allowed): ")
			if secret == "": break
			try:
				secret = "".join(secret.strip().split())
				totp(secret)
				secrets[label] = secret
				break
			except (TypeError, binascii.Error):
				click.echo("No: invalid base32 secret")
		if secret != "":
			store.save_secrets(secrets)
			subprocess.call(['tput', 'reset'])
			click.echo("Secret stored with label '{}'".format(label))

@cli.command(name='rename')
@click.argument('label')
@click.argument('new_label')
def renamecmd(label, new_label):
	"""Rename the label of a secret in store"""
	store = Store()
	secrets = store.load_secrets()
	try: secrets[label]
	except KeyError:
		raise click.ClickException("label '{}' doesn't exist".format(label))
	else:
		try: secrets[new_label]
		except:
			secrets[new_label] = secrets[label]
			del secrets[label]
			store.save_secrets(secrets)
			click.echo("Label '{}' renamed to '{}'".format(label, new_label))
		else:
			raise click.ClickException("label '{}' already exists".format(new_label))

@cli.command(name='remove')
@click.argument('label')
@click.option('--confirm', is_flag=True,
		prompt="Are you sure you want to remove this label?",
		help="Option --confirm is required for remove")
def rmcmd(label, confirm):
	"""Remove secret: --confirm option will force!"""
	store = Store()
	secrets = store.load_secrets()
	if not secrets[label]:
		raise click.ClickException("label '{}' does not exist".format(label))
	elif not confirm:
		raise click.ClickException("--confirm option will force removal")
	else:
		del secrets[label]
		store.save_secrets(secrets)
		click.echo("Secret and label '{}' removed".format(label))

@cli.command(name='secret')
@click.argument('label')
def secretcmd(label):
	"""Display secret"""
	store = Store()
	secrets = store.load_secrets()
	secret = secrets.get(label)
	if secret:
		click.echo('{}: {}'.format(label, secret.upper()))
		click.pause("Press a key to clear the screen")
		subprocess.call(['tput', 'reset'])
	else:
		raise click.ClickException("label '{}' does not exist".format(label))

@cli.command(name='qr')
@click.argument('label')
@click.option('--invert', '-i', is_flag=True,
		help="White on black instead")
def qrcmd(label, invert):
	"""Display QR code for secret"""
	store = Store()
	secrets = store.load_secrets()
	secret = secrets.get(label)
	if secret:
		# Google URI: 'otpauth://totp/ISSUER:ACCT?secret=SECRET&issuer=ISSUER'
		qr = pyqrcode.create('otpauth://totp/o?secret={}'.format(secret.lower()),
				error='L')
		if invert:
			click.echo(qr.terminal(module_color='white', background='black',
					quiet_zone=1))
		else:
			click.echo(qr.terminal(module_color='black', background='white',
					quiet_zone=1))
		click.pause("Press a key to clear the screen")
		subprocess.call(['tput', 'reset'])
	else:
		raise click.ClickException("label '{}' does not exist".format(label))

@cli.command(name='password')
def passwdcmd():
	"""Set password (empty: no encryption!)"""
	store = Store()
	secrets = store.load_secrets()
	newpasswd = getpass.getpass("Enter new store password: ")
	confirmpasswd = getpass.getpass("Confirm new store password: ")
	if not newpasswd == confirmpasswd:
		raise click.ClickException("passwords not matching")
	store.save_secrets(secrets, newpasswd)
	click.echo("New password set")
