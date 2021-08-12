import click
import csv
import io
from numpy import heaviside
import pandas as pd
import re
import datetime
from dateutil.relativedelta import relativedelta


@click.group()
def payslip():
    pass


@payslip.command()
@click.argument("filename", type=click.File(encoding="shift_jis"))
def tocsv(filename):

    # 賃金台帳の各種従業員情報の最終行
    COL_PAYROLL_EMPLOYEE_INFO = 7

    header = ""
    body = ""

    for i, f in enumerate(filename):
        if i < COL_PAYROLL_EMPLOYEE_INFO:
            header += f
        else:
            body += f

    # reader = csv.reader(io.StringIO(body))
    # for row in reader:
    #     click.echo(row)

    head_reader = csv.reader(io.StringIO(header))
    for row in head_reader:
        if "集計期間" in row:
            _rrr = re.sub(r'（(.*) 〜 .*）', r'\1', row[1])
            _rr = re.sub(r'[年月日]', r' ', _rrr).split()
            _r = map(int, _rr)
#            click.echo(datetime.datetime(*_r) + relativedelta(months=1))
            start_date = datetime.datetime(*_r)
            click.echo(start_date)
            break

    body_reader = csv.reader(io.StringIO(body))
    for row in body_reader:
        click.echo(len(row))
        _aaa = [start_date + relativedelta(months=i) for i,
                _ in enumerate(range(len(row) - 2))]
        click.echo(_aaa)
        # click.echo(','.join(_aaa))
        break

    df = pd.read_csv(io.StringIO(body), index_col=0)
    click.echo(df)


def payroll_check(filename):
    c = csv.reader(filename)
    for row in c:
        click.echo(row)
