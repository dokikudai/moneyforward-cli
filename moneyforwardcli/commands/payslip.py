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
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)
click_logging.basic_config(logger)


@click.group()
def payslip():
    pass


class OutJournals(Enum):
    COL_1 = "取引No"
    COL_2 = "取引日"
    COL_3 = "借方勘定科目"
    COL_4 = "借方補助科目"
    COL_5 = "借方税区分"
    COL_6 = "借方部門"
    COL_7 = "借方金額(円)"
    COL_8 = "借方税額"
    COL_9 = "貸方勘定科目"
    COL_10 = "貸方補助科目"
    COL_11 = "貸方税区分"
    COL_12 = "貸方部門"
    COL_13 = "貸方金額(円)"
    COL_14 = "貸方税額"
    COL_15 = "摘要"
    COL_16 = "仕訳メモ"
    COL_17 = "タグ"
    COL_18 = "MF仕訳タイプ"
    COL_19 = "決算整理仕訳"
    COL_20 = "作成日時"
    COL_21 = "最終更新日時"


class CustomItem(Enum):
    SALARY_PAYMENT_DATE = "給与支払日"
    PAYROLL_CLOSING_DATE = "給与計算締日"
    DEPARTMENT = "部門"


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

    custom_rows = create_custom_date(body, get_custom_parts(head_reader))
    body = custom_rows + body

    df = pd.read_csv(io.StringIO(body), index_col=0)
    # click.echo(df.dropna(how="all"))

    env_df = pd.read_csv("./.env/csv.csv", index_col=0)
    # click.echo(env_df.loc["基本給(支給)", "摘要"])
    # csv_eval(env_df.loc["基本給(支給)", "摘要"])
    dict_df = {label: s.replace("0", np.nan).dropna() for label, s in df.iteritems()}
    click.echo(dict_df["2020年07月度"])

    _dict_df = dict_df["2020年07月度"]
    _dict_df.replace("0", np.nan)

    click.echo(f'_dict_df: {_dict_df}')

    list_custom_item = [i.value for i in CustomItem]
    rev_custom_item = {e.value: e.name for e in CustomItem}
    click.echo(rev_custom_item)
    payslip_item = {}

    for idx in _dict_df.index.values:
        if idx in env_df.index:
            for oj in OutJournals:
                #click.echo(f"oj: {oj}")

                if oj.value == OutJournals.COL_1.value:
                    click.echo(f'idx: {idx}, oj.value: {oj.value}')
                    # click.echo(f'idx: {idx}, v: {_dict_df[idx]}')
                    click.echo(env_df.loc[idx, oj.value])
                
                if oj.value == OutJournals.COL_2.value:
                    click.echo(env_df.loc[idx, oj.value])


        if idx in list_custom_item:
            click.echo(f'CustomItem: {idx}')
            payslip_item[rev_custom_item[idx]] = _dict_df[idx]


def csv_eval(row):
    f_string = "f'" + row + "'"
    click.echo(f'f_string: {f_string}')

    exec_f = eval(f_string, None, {'yyyymm': "2021年7月度", 'depertment': "部門A"})
    click.echo(exec_f)
    return exec_f


def create_custom_date(body, custom_parts):
    header = [""]
    custom_row_1 = [CustomItem.SALARY_PAYMENT_DATE.value]
    custom_row_2 = [CustomItem.PAYROLL_CLOSING_DATE.value]
    custom_row_3 = [CustomItem.DEPARTMENT.value]

    reader = csv.reader(io.StringIO(body))
    for i, r in enumerate(reader):
        if i == 0:
            _o = [i.split("\n") for i in r]
            logger.debug(f"_o: {_o}")

            for i, data in enumerate(_o):
                # 空（一番先頭のnullのケース）
                if len(data) == 1 and not data[0]:
                    continue

                # 月度項目のケース（月日の文字列編集）
                if len(data) > 1 and "月度" in data[0]:
                    num_start_month = int(re.sub(r'[ 月度]', r'', data[0]))

                    logger.debug(
                        f"num_start_month: {num_start_month}, data[1]: {data[1]}")

                    cnt_month = i - 1
                    dt_base = custom_parts.get(
                        "start_date") + relativedelta(months=cnt_month)
                    dt_pay = (
                        dt_base +
                        relativedelta(months=1) -
                        relativedelta(days=1)
                    )

                    if num_start_month != int(dt.strftime(dt_pay, "%m")):
                        logger.error("CSVヘッダー月不整合")
                        exit(1)

                    header.append(dt.strftime(dt_pay, "%Y年%m月度"))
                    custom_row_1.append(dt.strftime(dt_pay, "%Y/%m/%d"))
                    custom_row_2.append(
                        dt.strftime(
                            dt_base -
                            relativedelta(
                                days=1),
                            "%Y/%m/%d"))
                    custom_row_3.append(custom_parts.get("depertment"))

                    continue

                # 賞与があるケース
                if len(data) > 1 and data[0] == "賞与":
                    header.append(f"賞与 {data[1]}")
                    dt_bounus_base = dt.strptime(data[1], "%Y/%m/%d")
                    dt_bounus_pay = (
                        dt_bounus_base +
                        relativedelta(days=1) +
                        relativedelta(months=1) -
                        relativedelta(days=1)
                    )
                    custom_row_1.append(dt.strftime(dt_bounus_pay, "%Y/%m/%d"))
                    custom_row_2.append(data[1])
                    custom_row_3.append(custom_parts.get("depertment"))

                    continue

                # 最終の項目の合計
                if len(data) == 1 and data[0] == "合計":
                    header.append(data[0])
                    custom_row_1.append("")
                    custom_row_2.append("")
                    custom_row_3.append(custom_parts.get("depertment"))

                    continue

                # すべてのifをこえてこれが実行されると考慮外のケースがありうる
                logger.error(f"考慮漏れ項目の可能性があります。 data: {data}")
                exit(1)

    logger.debug(f"header: {header}")
    logger.debug(f"custom_row_1: {custom_row_1}")
    logger.debug(f"custom_row_2: {custom_row_2}")
    logger.debug(f"custom_row_3: {custom_row_3}")

    custom_rows = ""
    for i in [header, custom_row_1, custom_row_2, custom_row_3]:
        custom_rows += (",".join(i) + "\n")

    logger.debug(f"custom_rows: {custom_rows}")

    return custom_rows


def get_custom_parts(head_reader):
    return {
        "start_date": get_start_date(head_reader),
        "depertment": get_depertment(head_reader)
    }


def get_start_date(head_reader):
    for row in head_reader:
        if "集計期間" in row[0]:
            _strdt = re.sub(r'（(.*) 〜 .*）', r'\1', row[1])
            strdt = dt.strptime(_strdt, "%Y年%m月%d日")
            logger.debug(f"strdt: {strdt}")
            return strdt

    logger.error("get_start_date")


def get_depertment(head_reader):
    for row in head_reader:
        if "部門" in row:
            return row[1]

    logger.error("get_depertment")
