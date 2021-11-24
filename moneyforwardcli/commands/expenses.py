import logging
import click
import click_logging


logger = logging.getLogger(__name__)
click_logging.basic_config(logger)


@click.group()
def expenses():
    """actionコマンド
    """

@expenses.command()
@click.argument("filename", type=click.File(encoding="shift_jis"))
@click_logging.simple_verbosity_option(logger)
def to_journal_csv(filename):
    pass
