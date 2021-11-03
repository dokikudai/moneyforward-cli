"""
マネーフォワードクラウド会計 給与オリジナル仕訳CSV出力
"""
import io
import csv
import re
from datetime import datetime as dt
import logging
from enum import Enum
from typing import List
import click
import pandas as pd
from pandas.core.frame import DataFrame
from dateutil.relativedelta import relativedelta
import click_logging
import numpy as np


logger = logging.getLogger(__name__)
click_logging.basic_config(logger)


@click.group()
def payslip():
    """actionコマンド
    """


class OutJournals(Enum):
    """出力CSV仕訳enum
    """
    COL_01 = ("取引No", "")
    COL_02 = ("取引日", "")
    COL_03 = ("借方勘定科目", "")
    COL_04 = ("借方補助科目", "")
    COL_05 = ("借方税区分", "")
    COL_06 = ("借方部門", "")
    COL_07 = ("借方金額(円)", "")
    COL_08 = ("借方税額", "")
    COL_09 = ("貸方勘定科目", "")
    COL_10 = ("貸方補助科目", "")
    COL_11 = ("貸方税区分", "対象外")
    COL_12 = ("貸方部門", "")
    COL_13 = ("貸方金額(円)", "")
    COL_14 = ("貸方税額", "")
    COL_15 = ("摘要", "")
    COL_16 = ("仕訳メモ", "")
    COL_17 = ("タグ", "")
    COL_18 = ("MF仕訳タイプ", "")
    COL_19 = ("決算整理仕訳", "")
    COL_20 = ("作成日時", "")
    COL_21 = ("最終更新日時", "")

    def __init__(self, col, default_val):
        self.col = col
        self.default_val = default_val

    def select_val(self, print_env_val, print_payroll_val, custom_item):
        if self is self.COL_01:
            return 1

        if self is self.COL_02:
            return custom_item[CustomItem.PAYROLL_CLOSING_DATE.value]

        if self is self.COL_06:
            return custom_item[CustomItem.DEPARTMENT.value]

        if self is self.COL_12:
            return custom_item[CustomItem.DEPARTMENT.value]

        if self is self.COL_15:
            # csv_eval(custom_item[CustomItem.SALARY_PAYMENT_DATE.value])
            return csv_eval(print_env_val, custom_item)

        if self is self.COL_07 or self is self.COL_13:
            return print_payroll_val

        if print_env_val is not np.nan:
            return print_env_val
        else:
            return self.default_val

    @classmethod
    def csv_header(cls):
        return [i.value[0] for i in cls]

    @classmethod
    def get_karikata_mibaraihiyo(cls) -> List[str]:
        _list = [
            cls.COL_03,
            cls.COL_04,
            cls.COL_05,
            cls.COL_06,
            cls.COL_07,
            cls.COL_08]
        return [i.value[0] for i in _list]

    @classmethod
    def get_kashikata_mibaraihiyo(cls) -> List[str]:
        _list = [
            cls.COL_09,
            cls.COL_10,
            cls.COL_11,
            cls.COL_12,
            cls.COL_13,
            cls.COL_14]
        return [i.value[0] for i in _list]

    def __str__(self):
        return f'name: {self.name}, value: {self.value}'


def csv_eval(row, custom_item):
    if not isinstance(row, str):
        return ""

    f_string = "f'" + row + "'"
    click.echo(f'f_string: {f_string}')

    exec_f = eval(
        f_string, None, {
            'yyyymm': to_jp_year_name(custom_item[CustomItem.SALARY_PAYMENT_DATE.value]),
            'sal_kbn': "給与",
            'depertment': custom_item[CustomItem.DEPARTMENT.value]
        }
    )
    click.echo(exec_f)
    return exec_f


def to_jp_year_name(yyyymmdd):
    _d = yyyymmdd.split('/')

    yyyy = int(_d[0])
    mm = _d[1].zfill(2)

    if yyyy > 2018:
        return f'令和{str(yyyy - 2018).zfill(2)}年{mm}月度'

    return f'{str(yyyy)}年{mm}月度'


class CustomItem(Enum):
    """Enum """
    START_DATE = 0
    SALARY_PAYMENT_DATE = "給与支払日"
    PAYROLL_CLOSING_DATE = "給与計算締日"
    DEPARTMENT = "部門"


COL_PAYROLL_EMPLOYEE_INFO = 7


@payslip.command()
@click.argument("filename", type=click.File(encoding="shift_jis"))
@click_logging.simple_verbosity_option(logger)
def to_journal_csv(filename):
    """賃金台帳の各種従業員情報の最終行
    """

    header = ""
    body = ""

    for i, line in enumerate(filename):
        if i < COL_PAYROLL_EMPLOYEE_INFO:
            header += line
        else:
            body += line

    df_head = pd.read_csv(io.StringIO(header))

    custom_ports = get_custom_parts(df_head)

    custom_rows = create_custom_data(body, custom_ports)
    body = custom_rows + body

    df = pd.read_csv(io.StringIO(body), index_col=0)
    dict_df = {label: s.replace("0", np.nan).dropna()
               for label, s in df.iteritems()}

    _dict_df = dict_df["賞与 2021/06/30"]
    _dict_df.replace("0", np.nan)

    df_custom_print: DataFrame = pd.read_csv("./.env/csv.csv", index_col=0)

    monthly_payslip = _dict_df.to_dict()

    custom_dic = _dict_df[CustomItem.SALARY_PAYMENT_DATE.value:
                          CustomItem.DEPARTMENT.value].to_dict()

    _index = df_custom_print.index
    _data = []
    for mp_key in monthly_payslip.keys():
        _p = [
            i.select_val(
                df_custom_print.at[mp_key, i.value[0]],
                monthly_payslip[mp_key],
                custom_dic
            )
            for i in OutJournals if mp_key in _index.values
        ]

        if len(_p):
            _data.append(_p)

    click.echo(_data)

    # マイナスデータの借方/貸方入れ替え
    _df_calc_1 = pd.DataFrame(_data, columns=OutJournals.csv_header())
    _df_calc_1 = _df_calc_1.astype({OutJournals.COL_07.value[0]: 'int'})
    _df_calc_1 = _df_calc_1.astype({OutJournals.COL_13.value[0]: 'int'})

    _karikata_vals = _df_calc_1[OutJournals.COL_07.value[0]]
    _kashikata_vals = _df_calc_1[OutJournals.COL_13.value[0]]

    # SettingWithCopyWarning 防止で copy 付加
    _select_minus = _df_calc_1[(_karikata_vals < 0)
                               | (_kashikata_vals < 0)].copy()
    _select_minus[OutJournals.COL_07.value[0]
                  ] = _select_minus[OutJournals.COL_07.value[0]] * -1
    _select_minus[OutJournals.COL_13.value[0]
                  ] = _select_minus[OutJournals.COL_13.value[0]] * -1

    click.echo(_select_minus)

    _kari_data = _select_minus[OutJournals.get_karikata_mibaraihiyo()]
    _kashi_data = _select_minus[OutJournals.get_kashikata_mibaraihiyo()]

    click.echo(_kashi_data)

    _select_minus[OutJournals.get_karikata_mibaraihiyo()] = _kashi_data
    _select_minus[OutJournals.get_kashikata_mibaraihiyo()] = _kari_data

    click.echo(_select_minus)

    _df_calc_1.iloc[_select_minus.index.tolist()] = _select_minus.copy()

    click.echo(_df_calc_1)

    # 未払費用の計算
    karikata_mibaraihiyo = _df_calc_1.groupby(
        [OutJournals.COL_03.value[0], OutJournals.COL_04.value[0]]).sum()
    kashikata_mibaraihiyo = _df_calc_1.groupby(
        [OutJournals.COL_09.value[0], OutJournals.COL_10.value[0]]).sum()

    _kari_mi = karikata_mibaraihiyo["借方金額(円)"]
    _kashi_mi = kashikata_mibaraihiyo["貸方金額(円)"]

    _calc_df = pd.concat([_kari_mi, _kashi_mi], axis=1).fillna(0)
    _calc_df["貸方-借方金額(円)"] = _calc_df["貸方金額(円)"] - _calc_df["借方金額(円)"]

    _calc_mibaraihiyo = _calc_df.loc["未払費用", "貸方-借方金額(円)"]
    click.echo(f'_calc_mibaraihiyo: {_calc_mibaraihiyo}')

    karikata_mibaraihiyo: int = _df_calc_1.groupby(
        OutJournals.COL_03.value[0]).sum().at['未払費用', OutJournals.COL_07.value[0]]
    kashikata_mibaraihiyo: int = _df_calc_1.groupby(
        OutJournals.COL_09.value[0]).sum().at['未払費用', OutJournals.COL_13.value[0]]
    mibaraihiyo: int = kashikata_mibaraihiyo - karikata_mibaraihiyo

    click.echo(
        f'{mibaraihiyo}, {kashikata_mibaraihiyo}, {karikata_mibaraihiyo}')

    # 未払費用の編集
    _df_edit_1 = _df_calc_1.copy()

    karikata_index: List[int] = _df_edit_1.index[_df_edit_1[OutJournals.COL_03.value[0]] == "未払費用"]
    karikata_column: List[int] = [_df_edit_1.columns.tolist().index(
        i) for i in OutJournals.get_karikata_mibaraihiyo()]

    kashikata_index: List[int] = _df_edit_1.index[_df_edit_1[OutJournals.COL_09.value[0]] == "未払費用"]
    kashikata_column: List[int] = [_df_edit_1.columns.tolist().index(
        i) for i in OutJournals.get_kashikata_mibaraihiyo()]

    _df_edit_1.iloc[karikata_index, karikata_column] = np.NaN
    _df_edit_1.iloc[kashikata_index, kashikata_column] = np.NaN

    click.echo(_df_edit_1)

    _calc_mibaraihiyo_data = get_df_mibaraihiyo(
        _df_edit_1,
        _calc_mibaraihiyo,
        custom_ports.get(CustomItem.DEPARTMENT)
    )

    _df_edit_1 = _df_edit_1.append(_calc_mibaraihiyo_data, ignore_index=True)
    click.echo(_df_edit_1)


def get_df_mibaraihiyo(df, df_calc_mibaraihiyo, department):
    # 未払費用data作成
    df_mi = pd.DataFrame(index=[], columns=df.columns)
    for i, v in df_calc_mibaraihiyo.items():
        _tmp = df.iloc[0, :].copy()
        _tmp_df = pd.DataFrame([_tmp])
        _tmp_df.loc[:, OutJournals.get_karikata_mibaraihiyo()] = np.NaN

        _tmp_df[OutJournals.COL_09.value[0]] = "未払費用"
        _tmp_df[OutJournals.COL_10.value[0]] = i
        _tmp_df[OutJournals.COL_11.value[0]] = "対象外"
        _tmp_df[OutJournals.COL_12.value[0]] = department
        _tmp_df[OutJournals.COL_13.value[0]] = v

        df_mi = df_mi.append(_tmp_df, ignore_index=True)

    return df_mi


def create_custom_data(body, custom_parts):
    header = [""]
    custom_row_1 = [CustomItem.SALARY_PAYMENT_DATE.value]
    custom_row_2 = [CustomItem.PAYROLL_CLOSING_DATE.value]
    custom_row_3 = [CustomItem.DEPARTMENT.value]

    reader = csv.reader(io.StringIO(body))
    for reader_index, r in enumerate(reader):
        if reader_index == 0:
            row_list = [i.split("\n") for i in r]
            logger.debug(f"row_list: {row_list}")

            for row_list_index, data in enumerate(row_list):
                # 空（一番先頭のnullのケース）
                if len(data) == 1 and not data[0]:
                    continue

                # 月度項目のケース（月日の文字列編集）
                if len(data) > 1 and "月度" in data[0]:
                    num_start_month = int(re.sub(r'[ 月度]', r'', data[0]))

                    logger.debug(
                        f"num_start_month: {num_start_month}, data[1]: {data[1]}")

                    cnt_month = row_list_index - 1

                    dt_base = custom_parts.get(
                        CustomItem.START_DATE) + relativedelta(months=cnt_month)
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
                    custom_row_3.append(
                        custom_parts.get(
                            CustomItem.DEPARTMENT))

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
                    custom_row_3.append(
                        custom_parts.get(
                            CustomItem.DEPARTMENT))

                    continue

                # 最終の項目の合計
                if len(data) == 1 and data[0] == "合計":
                    header.append(data[0])
                    custom_row_1.append("")
                    custom_row_2.append("")
                    custom_row_3.append(
                        custom_parts.get(
                            CustomItem.DEPARTMENT))

                    continue

                # すべてのifをこえてこれが実行されると考慮外のケースがありうる
                logger.error(f"考慮漏れ項目の可能性があります。 data: {data}")
                exit(1)

    custom_rows = ""
    for i in [header, custom_row_1, custom_row_2, custom_row_3]:
        custom_rows += (",".join(i) + "\n")

    return custom_rows


def get_custom_parts(df_head):
    return {
        CustomItem.START_DATE: get_start_date(df_head),
        CustomItem.DEPARTMENT: df_head.at['部門', '賃金台帳'],
        CustomItem.PAYROLL_CLOSING_DATE: "",
        'sal_kbn': get_salary_kbn(df_head)
    }


def get_start_date(df_head):
    date_string = re.sub(r'（(.*) 〜 .*）', r'\1', df_head.at['集計期間', '賃金台帳'])
    start_dt = dt.strptime(date_string, "%Y年%m月%d日")
    logger.debug(f"start_dt: {start_dt}")
    return start_dt


def get_salary_kbn(df_head):
    if "賞与" in df_head.at['集計期間', '賃金台帳']:
        return "賞与"

    return "給与"
