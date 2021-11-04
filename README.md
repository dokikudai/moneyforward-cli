# moneyforward-cli 初期設定

## 必要ライブラリのインストール
```
pip install -r requirements.txt
```

## ローカル環境にインストール
Linuxサーバ上にローカルインストール。  
setup.pyがある場所で以下実行
```
pip install -e .
```

## コマンドオプションの保管適用
[Shell Completion — Click Documentation (8.0.x)](https://click.palletsprojects.com/en/8.0.x/shell-completion/)
```
eval "$(_MONEYFORWARD_COMPLETE=bash_source moneyforward)"
```

# コマンドサンプル
```
moneyforward payslip to-journal-csv .env/payroll_book_report_3_野極武.csv --verbosity
```