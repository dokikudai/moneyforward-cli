from types import LambdaType
import click
import csv
import io
import pandas as pd
import re
from datetime import datetime as dt, timedelta
from dateutil.relativedelta import relativedelta
import logging
import click_logging
from monthdelta import monthmod


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
 
    custom_header = create_custom_date(body, get_start_date(head_reader))
    body = custom_header + body

    df = pd.read_csv(io.StringIO(body), index_col=0)
    click.echo(df)


def create_custom_date(body, start_date):
    _hdata = [""]
    logger.debug(f"_hdata_f: {_hdata}")
    _hspdate = ["給与支払日"]
    logger.debug(f"_hspdate_f: {_hspdate}")
    _hsedate = ["給与計算締日"]

    reader = csv.reader(io.StringIO(body))
    for i, r in enumerate(reader):
        if i == 0:
            _o = [i.split("\n") for i in r]
            logger.debug(f"_o: {_o}")

            for i, data in enumerate(_o):
                # 月日の文字列編集のため
                if len(data) > 1:
                    if re.search("月度", data[0]):
                        num_start_month = int(re.sub(r'[ 月度]', r'', data[0]))

                        logger.debug(f"num_start_month: {num_start_month}, data[1]: {data[1]}")
                        
                        cnt_month = i - 1
                        dt_base = start_date + relativedelta(months=cnt_month)
                        dt_pay = (
                            dt_base + 
                            relativedelta(months=1) - 
                            relativedelta(days=1)
                        )

                        if num_start_month != int(dt.strftime(dt_pay, "%m")):
                            logger.error("CSVヘッダー月不整合")
                            exit(1)

                        _hdata.append(dt.strftime(dt_pay, "%Y年%m月度"))
                        _hspdate.append(dt.strftime(dt_pay, "%Y/%m/%d"))
                        _hsedate.append(dt.strftime(dt_base - relativedelta(days=1), "%Y/%m/%d"))


                if len(data) > 1 and data[0] == "賞与":
                    _hdata.append(f"賞与 {data[1]}")
                    dt_bounus_end = dt.strptime(data[1], "%Y/%m/%d")
                    dt_bounus_pay = (
                        dt_bounus_end + 
                        relativedelta(days=1) + 
                        relativedelta(months=1) - 
                        relativedelta(days=1)
                    )
                    _hspdate.append(dt.strftime(dt_bounus_pay, "%Y/%m/%d"))
                    _hsedate.append(data[1])

                if len(data) == 1 and data[0] == "合計":
                    _hdata.append(data[0])
                    _hspdate.append("")
                    _hsedate.append("")

    logger.debug(f"_hdata: {_hdata}")
    logger.debug(f"_hspdate: {_hspdate}")
    logger.debug(f"_hsedate: {_hsedate}")

    _headers = ""
    for i in [_hdata, _hspdate, _hsedate]:
        _headers += (", ".join(i) + "\n")
        
    logger.debug(f"_headers: {_headers}")

    return _headers


def get_start_date(head_reader):
    for row in head_reader:
        if "集計期間" in row[0]:
            _strdt = re.sub(r'（(.*) 〜 .*）', r'\1', row[1])
            strdt = dt.strptime(_strdt, "%Y年%m月%d日")
            logger.debug(f"strdt: {strdt}")
            return strdt


def get_depertment(head_reader):
    for row in head_reader:
        if "部門" in row:
            return row[1]

    logger.error("get_depertment")
