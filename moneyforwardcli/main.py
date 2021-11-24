import click
from moneyforwardcli.commands.payslip import payslip
from moneyforwardcli.commands.expenses import expenses

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


cli.add_command(payslip)
cli.add_command(expenses)
