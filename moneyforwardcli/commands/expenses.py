import logging
import click
import click_logging
import csv
import pandas as pd
from datetime import datetime as dt
from moneyforwardcli.commands.out_journals import MoneyForwardCloudJournals as mfcj
from moneyforwardcli.commands.out_journals import FreeeJournals as fj


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

    df_freee = pd.read_csv(filename)

    _summary_column = [i.value for i in fj.summary_column()]

    kanri_numbers: List = []

    # "申請番号" ～ "メモタグ"項目が 全て NaN かどうか
    kanri_number = 0
    for idx, is_null in df_freee.loc[:, _summary_column].isnull().all(axis=1).items():
        _i = 0
        kanri_number = kanri_number + 1
        if is_null:
            df_freee.loc[idx: idx,  _summary_column] = df_freee.loc[(idx - 1): (idx - 1), _summary_column].values
            _i = _i + 1
            kanri_number = kanri_number - _i

        kanri_numbers.append(kanri_number)

    df_freee[fj.COL_02.value] = kanri_numbers

    # str -> 日付変換
    df_freee[fj.COL_03.value] = pd.to_datetime(df_freee[fj.COL_03.value])

    # 日付絞り込み
    df_freee = df_freee[
        (df_freee[fj.COL_03.value] >= dt.strptime("2020/06/01", "%Y/%m/%d")) &
        (df_freee[fj.COL_03.value] <= dt.strptime("2021/05/31", "%Y/%m/%d"))
    ]

    # 日付 -> str 変換
    df_freee[fj.COL_03.value] = df_freee[fj.COL_03.value].dt.strftime('%Y/%m/%d')
    df_freee = df_freee.reset_index(drop=True)

    # df_freee の 管理番号 項目で計算
    


    # マネーフォワード用 データフレーム作成
    df_mfc = pd.DataFrame(columns=mfcj.csv_header())

    df_mfc[mfcj.COL_01.value] = df_freee[fj.COL_02.value]
    df_mfc[mfcj.COL_02.value] = df_freee[fj.COL_03.value]
    df_mfc[mfcj.COL_03.value] = df_freee[fj.COL_06.value]
    df_mfc[mfcj.COL_04.value] = ""
    df_mfc[mfcj.COL_05.value] = "対象外"
    df_mfc[mfcj.COL_06.value] = df_freee[fj.COL_13.value]
    df_mfc[mfcj.COL_07.value] = df_freee[fj.COL_08.value]
    df_mfc[mfcj.COL_09.value] = "未払金"
    df_mfc[mfcj.COL_10.value] = df_freee[fj.COL_13.value]
    df_mfc[mfcj.COL_11.value] = df_freee[fj.COL_13.value]
    df_mfc[mfcj.COL_11.value] = df_freee[fj.COL_07.value]
    df_mfc[mfcj.COL_13.value] = df_freee[fj.COL_08.value]
    df_mfc[mfcj.COL_15.value] = df_freee[fj.COL_11.value]

    click.echo(df_mfc.to_csv(index=False, quoting=csv.QUOTE_NONNUMERIC))

    df_mfc.to_csv('import_立替経費_2020年度.csv', index=False, quoting=csv.QUOTE_NONNUMERIC)