import logging
import click
import click_logging
import pandas as pd
from enum import Enum
from datetime import datetime as dt


logger = logging.getLogger(__name__)
click_logging.basic_config(logger)


@click.group()
def expenses():
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

    @classmethod
    def csv_header(cls):
        return [i.value[0] for i in cls]

    def __str__(self):
        return f'name: {self.name}, value: {self.value}'


@expenses.command()
@click.argument("filename")
@click_logging.simple_verbosity_option(logger)
def to_journal_csv(filename):

    df_freee = pd.read_csv(filename)

    # str -> 日付変換
    df_freee['日付'] = pd.to_datetime(df_freee['日付'])

    # 日付絞り込み
    df_cp = df_freee[
        (df_freee["日付"] >= dt.strptime("2020/06/01", "%Y/%m/%d")) &
        (df_freee["日付"] <= dt.strptime("2021/05/31", "%Y/%m/%d"))
    ]

    # 日付 -> str 変換
    df_cp['日付'] = df_cp['日付'].dt.strftime('%Y/%m/%d')
    df_cp = df_cp.reset_index(drop=True)

    # "申請番号" ～ "メモタグ"項目が 全て NaN かどうか
    for idx, is_null in df_cp.loc[:, "申請番号":"メモタグ"].isnull().all(axis=1).items():
        if is_null:
            df_cp.loc[idx: idx, "申請番号":"メモタグ"] = df_cp.loc[(idx - 1): (idx - 1), "申請番号": "メモタグ"].values

    df_in = pd.DataFrame(columns=OutJournals.csv_header())

    df_in["取引日"] = df_cp["日付"]
    df_in["適用"] = df_cp["内容"]
    df_in["貸方勘定科目"] = "未払金"
    df_in["貸方補助科目"] = ""
    df_in["貸方税区分"] = "対象外"
    df_in["借方勘定科目"] = df_cp["経費科目"]
    df_in["貸方補助科目"] = df_cp["申請者"]
    df_in["借方金額(円)"] = df_cp["金額"]
    df_in["貸方金額(円)"] = df_cp["金額"]

    click.echo(df_in)