@echo off
echo 🚀 シフト分析システム フル機能化開始...
echo.

echo 📦 Step 1: 基本依存関係インストール...
pip install --upgrade pip
pip install dash==2.14.1
pip install plotly==5.17.0
pip install pandas==2.1.1
pip install numpy==1.24.3

echo.
echo 📊 Step 2: データ処理・分析ライブラリ...
pip install scipy==1.11.3
pip install scikit-learn==1.3.0
pip install openpyxl==3.1.2
pip install xlsxwriter==3.1.9

echo.
echo 🎨 Step 3: UI・可視化強化...
pip install dash-bootstrap-components==1.5.0
pip install dash-table==5.0.0
pip install kaleido==0.2.1

echo.
echo 🔧 Step 4: 開発・テスト支援...
pip install pytest==7.4.2
pip install flask==2.3.3
pip install gunicorn==21.2.0

echo.
echo ⚡ Step 5: パフォーマンス最適化...
pip install redis==5.0.0
pip install celery==5.3.2

echo.
echo 🛡️ Step 6: セキュリティ・監視...
pip install cryptography==41.0.4
pip install python-dotenv==1.0.0

echo.
echo ✅ 依存関係インストール完了!
echo 🎯 次は verify_installation.py を実行してください
pause