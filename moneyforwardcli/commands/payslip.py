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
    create_custom_date(body, get_start_date(head_reader))
    custom_date = get_custom_data(head_reader)

    body = custom_date + body

    df = pd.read_csv(io.StringIO(body), index_col=0)
    click.echo(df)


def payroll_check(filename):
    c = csv.reader(filename)
    for row in c:
        click.echo(row)


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
                if len(data) > 1:
                    if re.search("月度", data[0]):
                        num_start_month = int(re.sub(r'[ 月度]', r'', data[0]))
                        logger.debug(num_start_month)
                        logger.debug(data[1])
                        cnt_date = i - 1
                        _hdata.append(
                            dt.strftime(
                                start_date +
                                relativedelta(months=cnt_date),
                                "%Y年%m月度"))

                        _hspdate.append(
                            dt.strftime(
                                start_date +
                                relativedelta(months=cnt_date) +
                                relativedelta(months=1) -
                                relativedelta(days=1),
                                "%Y/%m/%d"))

                        _hsedate.append(
                            dt.strftime(
                                start_date +
                                relativedelta(months=cnt_date) -
                                relativedelta(days=1),
                                "%Y/%m/%d"))


                if len(data) > 1 and data[0] == "賞与":
                    _hdata.append(f"賞与 {data[1]}")

                if len(data) == 1 and data[0] == "合計":
                    _hdata.append(data[0])
                    _hspdate.append("")
                    _hsedate.append("")

            

    logger.debug(f"_hdata: {_hdata}")
    logger.debug(f"_hspdate: {_hspdate}")
    logger.debug(f"_hsedate: {_hsedate}")


def get_start_date(head_reader):
    for row in head_reader:
        if "集計期間" in row[0]:
            _strdt = re.sub(r'（(.*) 〜 .*）', r'\1', row[1])
            strdt = dt.strptime(_strdt, "%Y年%m月%d日")
            logger.debug(f"strdt: {strdt}")
            return strdt


def get_custom_data(head_reader):
    logger.debug(head_reader)
    for row in head_reader:
        if "集計期間" in row[0]:
            _strdt = re.sub(r'（(.*) 〜 .*）', r'\1', row[1])
            _enddt = re.sub(r'（.* 〜 (.*)）', r'\1', row[1])
            _strdt = dt.strptime(_strdt, "%Y年%m月%d日")
            _enddt = dt.strptime(_enddt, "%Y年%m月%d日")
            # この月の差計算により日付データを作成するための
            # 繰り返し数を取得
            mmod = monthmod(_strdt, _enddt)[0].months
            logger.debug(f"_strdt: {_strdt}, _enddt: {_enddt}, mmod: {mmod}")
        if "部門" in row[0]:
            depertment = row[1]

    _header_data = [_strdt + relativedelta(months=i) for i in range(mmod + 1)]
    logger.debug(f"_header_data: {_header_data}")

    header_data = [i.strftime("%Y年%m月度") for i in _header_data]
    header_data.insert(0, "")
    header_data.append("合計")

    body_pay_date = [i + relativedelta(months=1) - relativedelta(days=1)
                     for i in _header_data
                     ]
    body_pay_date = [i.strftime("%Y/%m/%d") for i in body_pay_date]
    body_pay_date.insert(0, "給与支払日")
    body_pay_date.append("")

    body_end_date = [i - relativedelta(days=1) for i in _header_data]
    body_end_date = [i.strftime("%Y/%m/%d") for i in body_end_date]
    body_end_date.insert(0, "給与締日")
    body_end_date.append("")

    body_depertment = [depertment for _ in _header_data]
    body_depertment.insert(0, "部門")
    body_depertment.append(depertment)

    custom_list = [header_data, body_pay_date, body_end_date, body_depertment]
    custom_list = [", ".join(i) + "\n" for i in custom_list]
    logger.debug(f"custom_list: {custom_list}")

    _c = ""
    for c in custom_list:
        _c = _c + c

    logger.debug(f"_c: {_c}")
    return _c


# def get_start_date(head_reader):
#     for row in head_reader:
#         if "集計期間" in row:
#             _rrr = re.sub(r'（(.*) 〜 .*）', r'\1', row[1])
#             _rr = re.sub(r'[年月日]', r' ', _rrr).split()
#             _r = map(int, _rr)
#             return dt(*_r)

#     logger.error("get_start_date")


def get_depertment(head_reader):
    for row in head_reader:
        if "部門" in row:
            return row[1]

    logger.error("get_depertment")


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
        logger.debug(date_body1)

        date_body2 = [
            (start_date +
             relativedelta(months=i) -
             relativedelta(days=1)
             ).strftime("%Y/%m/%d") for i in range(len(row) - 2)]
        date_body2.insert(0, "給与計算締日")
        date_body2.append("")
        logger.debug(date_body2)

        date_body3 = [
            'a' for _ in range(len(row) - 1)]
        date_body3.insert(0, "部門")

        break

    d1 = ", ".join(date_header)
    d2 = ",".join(date_body1)
    d3 = ",".join(date_body2)
    return f"{d1}\n{d2}\n{d3}\n"
