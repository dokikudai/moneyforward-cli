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
from pandas.core.series import Series


logger = logging.getLogger(__name__)
click_logging.basic_config(logger)

COL_PAYROLL_EMPLOYEE_INFO: int = 7


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

    def select_val(
            self,
            number,
            print_env_val,
            print_payroll_val,
            series_monthly_sal: Series):
        if self is self.COL_01:
            return number

        if self is self.COL_02:
            return series_monthly_sal[CustomItem.PAYROLL_CLOSING_DATE.value]

        if self is self.COL_04:
            return col_04or10_eval(print_env_val, series_monthly_sal)

        if self is self.COL_06:
            return series_monthly_sal[CustomItem.DEPARTMENT.value]

        if self is self.COL_09:
            return col_09_eval(print_env_val, series_monthly_sal)

        if self is self.COL_10:
            return col_04or10_eval(print_env_val, series_monthly_sal)

        if self is self.COL_12:
            return series_monthly_sal[CustomItem.DEPARTMENT.value]

        if self is self.COL_15:
            # csv_eval(custom_item[CustomItem.SALARY_PAYMENT_DATE.value])
            return col_15_eval(print_env_val, series_monthly_sal)

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


def col_09_eval(row, series_monthly_sal: Series):
    if not isinstance(row, str):
        return ""

    f_string = "f'" + row + "'"

    exec_f = eval(
        f_string, None, {
            'depertment': series_monthly_sal[CustomItem.DEPARTMENT.value]
        }
    )

    # TODO: 微妙なので直したい
    if exec_f == '未払費用（労働保険）' or exec_f == '未払金（労働保険）':

        # 2020年04月～2021年03月を遇、2021年04月～2022年03月を奇という風に繰り返し
        dt_pyroll_closeing_date = dt.strptime(series_monthly_sal[CustomItem.PAYROLL_CLOSING_DATE.value], "%Y/%m/%d")
        dt_year = (dt_pyroll_closeing_date + relativedelta(days=1)) - relativedelta(months=4)
        _year = dt_year.strftime('%Y')
        if int(_year) % 2:
            exec_f = exec_f + "奇"
        else:
            exec_f = exec_f + "偶"

    return exec_f


def col_04or10_eval(row, series_monthly_sal: Series):
    if not isinstance(row, str):
        return ""

    f_string = "f'" + row + "'"

    exec_f = eval(
        f_string, None, {
            'depertment': series_monthly_sal[CustomItem.DEPARTMENT.value]
        }
    )

    # TODO: 微妙なので直したい
    if exec_f == '所得税':
        month = series_monthly_sal[CustomItem.PAYROLL_CLOSING_DATE.value][5:7]
        if 6 <= int(month) <= 11:
            exec_f = exec_f + "（06～11月）"
        else:
            exec_f = exec_f + "（12～05月）"

    return exec_f


def col_15_eval(row, series_monthly_sal: Series):
    if not isinstance(row, str):
        return ""

    f_string = "f'" + row + "'"

    exec_f = eval(
        f_string, None, {
            'yyyymm': series_monthly_sal.name,
            'sal_kbn': series_monthly_sal[CustomItem.SALARY_KBN.value],
            'depertment': series_monthly_sal[CustomItem.DEPARTMENT.value]
        }
    )
    return exec_f


class CustomItem(Enum):
    """Enum """
    KEY = "KEY"
    START_DATE = 0
    SALARY_PAYMENT_DATE = "給与支払日"
    PAYROLL_CLOSING_DATE = "給与計算締日"
    DEPARTMENT = "部門"
    SALARY_KBN = "給与・賞与区分"

    @classmethod
    def get_create_customs(cls):
        return [
            cls.SALARY_PAYMENT_DATE,
            cls.PAYROLL_CLOSING_DATE,
            cls.DEPARTMENT,
            cls.SALARY_KBN
        ]


@payslip.command()
@click.argument("filename", type=click.File(encoding="shift_jis"))
@click_logging.simple_verbosity_option(logger)
def to_journal_csv(filename):
    """賃金台帳の各種従業員情報の最終行
    """

    _header: str = ""
    _body: str = ""

    for i, line in enumerate(filename):
        if i < COL_PAYROLL_EMPLOYEE_INFO:
            _header += line
        else:
            _body += line

    df_head = pd.read_csv(io.StringIO(_header))
    csv_info = get_csv_info(df_head)

    df_body = pd.read_csv(io.StringIO(_body))

    custom_rows = create_custom_data(df_body, csv_info)

#    click.echo(f'_body: {_body}')

    _body = custom_rows + _body

    df_body: DataFrame = pd.read_csv(io.StringIO(_body), index_col=0)
    dict_df = {label: s.replace("0", np.nan).dropna()
               for label, s in df_body.iteritems()}

    months: DataFrame = pd.read_csv(io.StringIO(custom_rows), index_col=0)

    list_months = [m for m in months.columns if m != "合計"]
#    click.echo(f'list_months: {list_months}')

    list_payslip: List = []

    for idx, i_month in enumerate(list_months):

        series_monthly_sal: Series = dict_df[i_month].replace("0", np.nan)
    #    series_monthly_sal: Series = dict_df["2021年05月期 決算賞与"].replace("0", np.nan)

        logger.debug(f'series_monthly_sal: {series_monthly_sal}')

        df_custom_print: DataFrame = pd.read_csv(
            "./.env/csv.csv", index_col=0, encoding="shift-jis")

        _data = []
        for key, value in series_monthly_sal.to_dict().items():
            _p = [
                i.select_val(
                    idx + 1,
                    df_custom_print.at[key, i.value[0]],
                    value,
                    series_monthly_sal
                ) for i in OutJournals if key in df_custom_print.index.values
            ]

            if len(_p):
                _data.append(_p)

        # マイナスデータの借方/貸方入れ替え
        _df_calc_1 = pd.DataFrame(_data, columns=OutJournals.csv_header())
        _df_calc_1 = _df_calc_1.astype({OutJournals.COL_07.value[0]: 'int'})
        _df_calc_1 = _df_calc_1.astype({OutJournals.COL_13.value[0]: 'int'})

        _karikata_vals = _df_calc_1[OutJournals.COL_07.value[0]]
        _kashikata_vals = _df_calc_1[OutJournals.COL_13.value[0]]

        # SettingWithCopyWarning 防止で copy 付加
        _select_minus = _df_calc_1[(_karikata_vals < 0) | (_kashikata_vals < 0)].copy()
        _select_minus[OutJournals.COL_07.value[0]] = _select_minus[OutJournals.COL_07.value[0]] * -1
        _select_minus[OutJournals.COL_13.value[0]] = _select_minus[OutJournals.COL_13.value[0]] * -1

        _kari_data = _select_minus[OutJournals.get_karikata_mibaraihiyo()]
        _kashi_data = _select_minus[OutJournals.get_kashikata_mibaraihiyo()]

        _select_minus[OutJournals.get_karikata_mibaraihiyo()] = _kashi_data
        _select_minus[OutJournals.get_kashikata_mibaraihiyo()] = _kari_data

        _df_calc_1.iloc[_select_minus.index.tolist()] = _select_minus.copy()

        # 未払費用の計算
        karikata_mibaraihiyo = _df_calc_1[_df_calc_1[OutJournals.COL_04.value[0]] == ""].groupby(
            [OutJournals.COL_03.value[0], OutJournals.COL_04.value[0]]).sum()
        kashikata_mibaraihiyo = _df_calc_1[_df_calc_1[OutJournals.COL_10.value[0]] == ""].groupby(
            [OutJournals.COL_09.value[0], OutJournals.COL_10.value[0]]).sum()

        _kari_mi = karikata_mibaraihiyo["借方金額(円)"]
        _kashi_mi = kashikata_mibaraihiyo["貸方金額(円)"]

        _calc_df = pd.concat([_kari_mi, _kashi_mi], axis=1).fillna(0)
        # np.nan 発生による float化 を int にキャスト
        _calc_df = _calc_df.astype({OutJournals.COL_07.value[0]: 'int'}).astype({
            OutJournals.COL_13.value[0]: 'int'})
        _calc_df["貸方-借方金額(円)"] = _calc_df["貸方金額(円)"] - _calc_df["借方金額(円)"]

        _calc_mibaraihiyo = _calc_df.loc["未払費用", "貸方-借方金額(円)"]

        # 未払費用の編集
        _df_edit_1 = _df_calc_1.copy()

        karikata_index: List[int] = _df_edit_1.index[_df_edit_1[OutJournals.COL_03.value[0]] == "未払費用"]
        karikata_column: List[int] = [_df_edit_1.columns.tolist().index(
            i) for i in OutJournals.get_karikata_mibaraihiyo()]

        kashikata_index: List[int] = _df_edit_1.index[
            (_df_edit_1[OutJournals.COL_09.value[0]] == "未払費用") &
            (_df_edit_1[OutJournals.COL_10.value[0]] == "")
        ]
        kashikata_column: List[int] = [_df_edit_1.columns.tolist().index(
            i) for i in OutJournals.get_kashikata_mibaraihiyo()]

        _df_edit_1.iloc[karikata_index, karikata_column] = ""
        _df_edit_1.iloc[kashikata_index, kashikata_column] = ""

        _calc_mibaraihiyo_data = get_df_mibaraihiyo(
            _df_edit_1,
            _calc_mibaraihiyo,
            series_monthly_sal
        )

        list_payslip.append(_df_edit_1.append(_calc_mibaraihiyo_data, ignore_index=True))
        # click.echo(_df_edit_1.to_csv(index=False, quoting=csv.QUOTE_NONNUMERIC))

    df_payslip: DataFrame = pd.concat(list_payslip)
    click.echo(df_payslip.to_csv(index=False, quoting=csv.QUOTE_NONNUMERIC))


def get_df_mibaraihiyo(df, df_calc_mibaraihiyo, series_monthly_sal: Series):
    # 未払費用data作成
    df_mi = pd.DataFrame(index=[], columns=df.columns)
    for i, v in df_calc_mibaraihiyo.items():
        _tmp = df.iloc[0, :].copy()
        _tmp_df = pd.DataFrame([_tmp])
        _tmp_df.loc[:, OutJournals.get_karikata_mibaraihiyo()] = ""

        _tmp_df[OutJournals.COL_09.value[0]] = "未払費用"
        _tmp_df[OutJournals.COL_10.value[0]] = i
        _tmp_df[OutJournals.COL_11.value[0]] = "対象外"
        _tmp_df[OutJournals.COL_12.value[0]
                ] = series_monthly_sal[CustomItem.DEPARTMENT.value]
        _tmp_df[OutJournals.COL_13.value[0]] = v
        _tmp_df[
            OutJournals.COL_15.value[0]
        ] = f"{series_monthly_sal.name} {series_monthly_sal[CustomItem.SALARY_KBN.value]} 差引支給額 {series_monthly_sal[CustomItem.DEPARTMENT.value]}"

        df_mi = df_mi.append(_tmp_df, ignore_index=True)

    return df_mi


def create_custom_data(df_body: DataFrame, csv_info):

    logger.debug(f'#create_custom_datad.f_body: {df_body}')

    df_custom: DataFrame = pd.DataFrame(
        index=[i.value for i in CustomItem.get_create_customs()]
    )

    monthly_cols = [i.split("\n") for i in df_body.columns]

    for monthly_index, monthly_val in enumerate(monthly_cols):
        # 空（一番先頭のnullのケース）
        if len(monthly_val) == 1 and monthly_val[0] == 'Unnamed: 0':
            continue

        # 月度項目のケース（月日の文字列編集）
        if len(monthly_val) > 1 and "月度" in monthly_val[0]:
            num_start_month = int(re.sub(r'[ 月度]', r'', monthly_val[0]))

            logger.debug(
                f"num_start_month: {num_start_month}, monthly_val[1]: {monthly_val[1]}")

            # 2つ目の monthly_index から月加算計算が必要になるため
            add_monthly = monthly_index - 1

            base_month = csv_info.get(
                CustomItem.START_DATE) + relativedelta(months=add_monthly)

            dt_pay = (
                base_month +
                relativedelta(months=1) -
                relativedelta(days=1)
            )

            # 月度不整合チェック
            if num_start_month != int(dt.strftime(dt_pay, "%m")):
                logger.error("CSVヘッダー月不整合")
                exit(1)

            df_custom[dt.strftime(dt_pay, "%Y年%m月度")] = [
                dt.strftime(dt_pay, "%Y/%m/%d"),
                dt.strftime(base_month - relativedelta(days=1), "%Y/%m/%d"),
                csv_info.get(CustomItem.DEPARTMENT),
                "給与"
            ]

            continue

        # 賞与があるケース
        if len(monthly_val) > 1 and monthly_val[0] == "賞与":

            logger.debug(
                f"monthly_val[1]: {monthly_val[1]}")

            dt_bounus_pay = dt.strptime(monthly_val[1], "%Y/%m/%d")
            dt_bounus_base = (
                dt_bounus_pay.replace(day=1) - relativedelta(days=1)
            )
            df_custom[f'{dt.strftime(dt_bounus_base, "%Y年%m月期")} 決算賞与'] = [
                dt.strftime(dt_bounus_pay, "%Y/%m/%d"),
                dt.strftime(dt_bounus_base, "%Y/%m/%d"),
                csv_info.get(CustomItem.DEPARTMENT),
                "決算賞与"
            ]

            continue

        # 最終の項目の合計
        if len(monthly_val) == 1 and monthly_val[0] == "合計":
            df_custom[monthly_val[0]] = [
                "",
                "",
                csv_info.get(CustomItem.DEPARTMENT),
                ""
            ]

            continue

        # すべてのifをこえてこれが実行されると考慮外のケースがありうる
        logger.error(f"考慮漏れ項目の可能性があります。 monthly_val: {monthly_val}")
        exit(1)

    logger.debug(f'df_custom.to_csv(): {df_custom.to_csv()}')

    return df_custom.to_csv()


def get_csv_info(df_head: DataFrame):
    return {
        CustomItem.START_DATE: get_start_date(df_head),
        CustomItem.DEPARTMENT: df_head.at['部門', '賃金台帳'],
        CustomItem.PAYROLL_CLOSING_DATE: ""
    }


def get_start_date(df_head):
    """ 年月日計算のベースになるYYYY/MM/DDを取得（）
    マネーフォワード賃金台帳ではYYYY年を取得できる項目がここしかないため
    ここで取得して、月度項目を横に1ヶ月加算計算にて更に他のYYYY年を計算
    """
    date_string = re.sub(r'（(.*) 〜 .*）', r'\1', df_head.at['集計期間', '賃金台帳'])
    start_dt = dt.strptime(date_string, "%Y年%m月%d日")
    return start_dt
