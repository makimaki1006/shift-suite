#!/bin/bash
# 依存関係インストールスクリプト
# IA1: pandas依存関係の解決

echo "🚀 シフト分析システム依存関係インストール開始..."
echo "📅 実行時刻: $(date)"

# Python環境確認
echo -e "\n📦 Python環境確認..."
python3 --version

# 必須パッケージリスト
echo -e "\n📋 インストール対象パッケージ:"
echo "  - pandas (データ分析基盤)"
echo "  - numpy (数値計算)"
echo "  - openpyxl (Excel読み書き)"
echo "  - scikit-learn (機械学習)"
echo "  - plotly (可視化)"
echo "  - dash (ダッシュボード)"

# pip更新
echo -e "\n🔧 pip更新..."
python3 -m pip install --upgrade pip

# 基本パッケージインストール
echo -e "\n📦 基本パッケージインストール..."
python3 -m pip install pandas numpy openpyxl

# 分析関連パッケージ
echo -e "\n📊 分析関連パッケージインストール..."
python3 -m pip install scikit-learn scipy statsmodels

# 可視化関連パッケージ
echo -e "\n📈 可視化関連パッケージインストール..."
python3 -m pip install plotly dash dash-bootstrap-components

# その他必要パッケージ
echo -e "\n🔧 その他必要パッケージインストール..."
python3 -m pip install xlrd xlwt python-dateutil pytz

# インストール確認
echo -e "\n✅ インストール確認..."
python3 -c "
import pandas
import numpy
import openpyxl
import sklearn
import plotly
import dash
print('✅ pandas version:', pandas.__version__)
print('✅ numpy version:', numpy.__version__)
print('✅ openpyxl version:', openpyxl.__version__)
print('✅ scikit-learn version:', sklearn.__version__)
print('✅ plotly version:', plotly.__version__)
print('✅ dash version:', dash.__version__)
"

echo -e "\n🎉 依存関係インストール完了!"
echo "📅 完了時刻: $(date)"