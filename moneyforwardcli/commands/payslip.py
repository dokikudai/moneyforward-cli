import click
import csv
import io
import pandas as pd
import re
import datetime
from dateutil.relativedelta import relativedelta
import logging
import click_logging


logger = logging.getLogger(__name__)
click_logging.basic_config(logger)


@click.group()
def payslip():
    pass


@payslip.command()
@click.argument("filename", type=click.File(encoding="shift_jis"))
@click_logging.simple_verbosity_option(logger)
def to_journal_csv(filename):

    # 賃金台帳の各種従業員情報の最終行
    COL_PAYROLL_EMPLOYEE_INFO = 7

    header = ""
    body = ""

    for i, f in enumerate(filename):
        if i < COL_PAYROLL_EMPLOYEE_INFO:
            header += f
        else:
            body += f

    head_reader = csv.reader(io.StringIO(header))
    start_date = get_start_date(head_reader)

    body_reader = csv.reader(io.StringIO(body))
    _head = create_date_header(start_date, body_reader)
    body = _head + body

    df = pd.read_csv(io.StringIO(body), index_col=0)
    click.echo(df)


def payroll_check(filename):
    c = csv.reader(filename)
    for row in c:
        click.echo(row)


def get_start_date(head_reader):
    for row in head_reader:
        if "集計期間" in row:
            _rrr = re.sub(r'（(.*) 〜 .*）', r'\1', row[1])
            _rr = re.sub(r'[年月日]', r' ', _rrr).split()
            _r = map(int, _rr)
            break
    return datetime.datetime(*_r)


def create_date_header(start_date, body_reader):
    """
    デフォルトの改行あり日付項目が扱いづらいのでYYYY/MM/DDに編集
    """
    for row in body_reader:
        date_header = [(start_date + relativedelta(months=i)
                        ).strftime("%Y年%m月度") for i in range(len(row) - 2)]
        date_header.insert(0, "")
        date_header.append("合計")

        logger.debug(f"start_date: {start_date}")
        logger.debug(f"row: {row}")
        logger.debug(f"date_header: {date_header}")

        date_body1 = [
            (start_date +
             relativedelta(months=i + 1) -
             relativedelta(days=1)
             ).strftime("%Y/%m/%d") for i in range(len(row) - 2)
        ]
        date_body1.insert(0, "給与支払日")
        date_body1.append("")

        date_body2 = [
            (start_date +
             relativedelta(months=i) -
             relativedelta(days=1)
             ).strftime("%Y/%m/%d") for i in range(len(row) - 2)]
        date_body2.insert(0, "給与計算締日")
        date_body2.append("")

        logger.debug(date_body1)
        logger.debug(date_body2)
        break

    d1 = ", ".join(date_header)
    d2 = ",".join(date_body1)
    d3 = ",".join(date_body2)
    return f"{d1}\n{d2}\n{d3}\n"
