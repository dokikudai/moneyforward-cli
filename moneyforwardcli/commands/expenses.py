import logging
import click
import click_logging
import pandas as pd
from datetime import datetime as dt
from moneyforwardcli.commands.out_journals import OutJournals as oj
from moneyforwardcli.commands.out_journals import MoneyForwardJournals as mfj


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
    
    

    # str -> 日付変換
    df_freee[oj.COL_02.value[0]] = pd.to_datetime(df_freee[oj.COL_02.value[0]])

    # 日付絞り込み
    df_cp = df_freee[
        (df_freee[oj.COL_02.value[0]] >= dt.strptime("2020/06/01", "%Y/%m/%d")) &
        (df_freee[oj.COL_02.value[0]] <= dt.strptime("2021/05/31", "%Y/%m/%d"))
    ]

    # 日付 -> str 変換
    df_cp[oj.COL_02.value[0]] = df_cp[oj.COL_02.value[0]].dt.strftime('%Y/%m/%d')
    df_cp = df_cp.reset_index(drop=True)

    _summary_column = [i.value for i in mfj.summary_column()]

    click.echo(df_cp)

    # "申請番号" ～ "メモタグ"項目が 全て NaN かどうか
    for idx, is_null in df_cp.loc[:, _summary_column].isnull().all(axis=1).items():
        if is_null:
            df_cp.loc[idx: idx,  _summary_column] = df_cp.loc[(idx - 1): (idx - 1), _summary_column].values

    df_in = pd.DataFrame(columns=oj.csv_header())

    click.echo(df_in)

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