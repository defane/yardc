import io
import click
import gpgme
import base64
from .config import config
from .core import Yardc

yardc = Yardc()

@click.group()
def cli():
    pass

@cli.command('hosts')
def cli_hosts():
    for host in yardc.hosts:
        click.echo("%s" % host)

@cli.command('machines')
@click.argument("host", type=click.Choice(yardc.hosts.keys()))
def cli_machines(host):
    host_obj = yardc.hosts[host]
    for machine in host_obj.machines:
        click.echo(machine)

@cli.command("status")
@click.argument("host", type=click.Choice(yardc.hosts.keys()))
@click.argument("machine")
def cli_status(host, machine):
    host_obj = yardc.hosts[host]
    machine = host_obj.machines[machine]
    click.echo(machine.status)

@cli.command('stop')
@click.argument("host", type=click.Choice(yardc.hosts.keys()))
@click.argument("machine")
def cli_stop(host, machine):
    host_obj = yardc.hosts[host]
    machine = host_obj.machines[machine]

    if machine.stop():
        click.echo("A shutdown of the machine %s was submitted." % machine.name)
    else:
        click.echo("Something wrong was ocurred during the shutdown of %s." % machine.name)

@cli.command('start')
@click.argument("host", type=click.Choice(yardc.hosts.keys()))
@click.argument("machine")
def cli_start(host, machine):
    host_obj = yardc.hosts[host]
    machine = host_obj.machines[machine]

    if machine.start():
        click.echo("The machine %s has been started." % machine.name)
    else:
        click.echo("Something was wrong during the start-up.")

@cli.command('rdp')
@click.argument("host", type=click.Choice(yardc.hosts.keys()))
@click.argument("machine")
def cli_start(host, machine):
    host_obj = yardc.hosts[host]
    machine = host_obj.machines[machine]
    machine.rdp()

@cli.command("encrypt_password")
def cli_encrypt_password():
    password = click.prompt("Password to encrypt", hide_input=True)
    plaintext = io.BytesIO(password.encode('utf-8'))
    encrypted = io.BytesIO()
    ctx = gpgme.Context()
    key = ctx.get_key(config['gpg'])
    ctx.encrypt([key], 0, plaintext, encrypted)
    click.echo(base64.encodebytes(encrypted.getvalue()).replace(b"\n", b''))
