from enum import Enum
from pandas.core.series import Series
from typing import List


class FreeeJournals(Enum):
    COL_01 = "収支区分"
    COL_02 = "管理番号"
    COL_03 = "発生日"
    COL_04 = "支払期日"
    COL_05 = "取引先"
    COL_06 = "勘定科目"
    COL_07 = "税区分"
    COL_08 = "金額"
    COL_09 = "税計算区分"
    COL_10 = "税額"
    COL_11 = "備考"
    COL_12 = "品目"
    COL_13 = "部門"
    COL_14 = "メモタグ（複数指定可、カンマ区切り）"
    COL_15 = "支払日"
    COL_16 = "支払口座"
    COL_17 = "支払金額"

    @classmethod
    def summary_column(cls):
        return [
            cls.COL_01,
            cls.COL_03,
            cls.COL_04,
            cls.COL_05,
        ]


class MoneyForwardCloudJournals(Enum):
    """出力CSV仕訳enum
    """
    COL_01 = "取引No"
    COL_02 = "取引日"
    COL_03 = "借方勘定科目"
    COL_04 = "借方補助科目"
    COL_05 = "借方税区分"
    COL_06 = "借方部門"
    COL_07 = "借方金額(円)"
    COL_08 = "借方税額"
    COL_09 = "貸方勘定科目"
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

    @classmethod
    def csv_header(cls):
        return [i.value for i in cls]
