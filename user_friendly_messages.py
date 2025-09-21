#!/usr/bin/env python3
"""
ユーザーフレンドリーなエラーメッセージとUI改善
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

class UserFriendlyMessages:
    """ユーザーフレンドリーなメッセージクラス"""

    @staticmethod
    def upload_error_messages():
        """アップロード関連のエラーメッセージ"""
        return {
            "file_too_large": {
                "title": "ファイルサイズが大きすぎます",
                "message": "アップロードできるファイルサイズは最大100MBまでです。\nファイルを圧縮するか、不要なデータを削除してから再度お試しください。",
                "icon": "📂",
                "color": "warning"
            },
            "invalid_format": {
                "title": "対応していないファイル形式です",
                "message": "ZIPファイル(.zip)のみアップロード可能です。\nファイル形式を確認して、ZIPファイルを選択してください。",
                "icon": "📄",
                "color": "warning"
            },
            "empty_file": {
                "title": "ファイルが空です",
                "message": "選択されたファイルにデータが含まれていません。\n正しいデータファイルを選択してください。",
                "icon": "📭",
                "color": "warning"
            },
            "corrupted_file": {
                "title": "ファイルが破損しています",
                "message": "ファイルを正しく読み込めませんでした。\nファイルが破損していないか確認して、再度アップロードしてください。",
                "icon": "⚠️",
                "color": "danger"
            },
            "no_analysis_data": {
                "title": "分析データが見つかりません",
                "message": "アップロードされたZIPファイルに分析用データが含まれていません。\napp.pyで生成された分析結果ZIPファイルをアップロードしてください。",
                "icon": "🔍",
                "color": "info"
            },
            "network_error": {
                "title": "通信エラーが発生しました",
                "message": "インターネット接続を確認して、再度お試しください。\n問題が続く場合は、しばらく時間をおいてから再度アクセスしてください。",
                "icon": "🌐",
                "color": "danger"
            }
        }

    @staticmethod
    def session_error_messages():
        """セッション関連のエラーメッセージ"""
        return {
            "session_expired": {
                "title": "セッションが期限切れです",
                "message": "セッションの有効期限が切れました。\nページを更新して、再度データをアップロードしてください。",
                "icon": "⏰",
                "color": "warning"
            },
            "session_conflict": {
                "title": "セッションエラーが発生しました",
                "message": "複数のタブで同時に操作された可能性があります。\nページを更新してから、再度お試しください。",
                "icon": "🔄",
                "color": "warning"
            }
        }

    @staticmethod
    def analysis_error_messages():
        """分析関連のエラーメッセージ"""
        return {
            "insufficient_data": {
                "title": "データが不足しています",
                "message": "この分析を実行するには、より多くのデータが必要です。\nより多くのシフトデータを含むファイルをアップロードしてください。",
                "icon": "📊",
                "color": "info"
            },
            "calculation_error": {
                "title": "計算エラーが発生しました",
                "message": "データの分析中にエラーが発生しました。\nデータ形式を確認して、再度お試しください。",
                "icon": "🧮",
                "color": "danger"
            },
            "memory_error": {
                "title": "メモリ不足です",
                "message": "データが大きすぎて処理できませんでした。\nデータを分割するか、不要な部分を削除してから再度お試しください。",
                "icon": "💾",
                "color": "warning"
            }
        }

    @staticmethod
    def create_error_card(error_type, error_key, details=None):
        """エラーカードコンポーネントを作成"""

        # エラーメッセージを取得
        all_messages = {}
        all_messages.update(UserFriendlyMessages.upload_error_messages())
        all_messages.update(UserFriendlyMessages.session_error_messages())
        all_messages.update(UserFriendlyMessages.analysis_error_messages())

        if error_key not in all_messages:
            # デフォルトエラーメッセージ
            message_data = {
                "title": "予期しないエラーが発生しました",
                "message": "申し訳ございませんが、システムエラーが発生しました。\nページを更新してから、再度お試しください。",
                "icon": "❌",
                "color": "danger"
            }
        else:
            message_data = all_messages[error_key]

        # 詳細情報があれば追加
        message_text = message_data["message"]
        if details:
            message_text += f"\n\n詳細: {details}"

        return dbc.Alert([
            html.Div([
                html.H4([
                    message_data["icon"], " ", message_data["title"]
                ], className="alert-heading"),
                html.P(message_text, style={'white-space': 'pre-line'}),
                html.Hr(),
                html.P([
                    "問題が解決しない場合は、",
                    html.A("こちら", href="#", className="alert-link"),
                    "からお問い合わせください。"
                ], className="mb-0 small")
            ])
        ], color=message_data["color"], dismissable=True)

    @staticmethod
    def create_success_message(action_type):
        """成功メッセージを作成"""
        success_messages = {
            "upload_complete": {
                "title": "アップロード完了",
                "message": "ファイルのアップロードが正常に完了しました。\n下記のタブから分析結果をご確認ください。",
                "icon": "✅"
            },
            "analysis_complete": {
                "title": "分析完了",
                "message": "データの分析が正常に完了しました。\n結果をダウンロードしたり、他のタブでより詳細な分析をご確認いただけます。",
                "icon": "📈"
            }
        }

        if action_type in success_messages:
            msg = success_messages[action_type]
            return dbc.Alert([
                html.H4([msg["icon"], " ", msg["title"]], className="alert-heading"),
                html.P(msg["message"], style={'white-space': 'pre-line'})
            ], color="success", dismissable=True)

        return None

    @staticmethod
    def create_info_message(info_type):
        """情報メッセージを作成"""
        info_messages = {
            "no_data": {
                "title": "データをアップロードしてください",
                "message": "分析を開始するには、まずZIPファイルをアップロードしてください。\n\n手順:\n1. 上部のアップロードエリアにZIPファイルをドラッグ&ドロップ\n2. または「ファイルを選択」をクリックしてファイルを選択\n3. アップロード完了後、各タブで分析結果を確認",
                "icon": "📤"
            },
            "processing": {
                "title": "データを処理中です",
                "message": "アップロードされたデータを分析しています。\nしばらくお待ちください...",
                "icon": "⏳"
            },
            "multi_user": {
                "title": "マルチユーザー対応",
                "message": "このシステムは複数のユーザーが同時に利用できます。\n各ユーザーのデータは安全に分離されており、他のユーザーのデータと混在することはありません。",
                "icon": "👥"
            }
        }

        if info_type in info_messages:
            msg = info_messages[info_type]
            return dbc.Alert([
                html.H4([msg["icon"], " ", msg["title"]], className="alert-heading"),
                html.P(msg["message"], style={'white-space': 'pre-line'})
            ], color="info")

        return None

    @staticmethod
    def create_loading_message():
        """ローディングメッセージを作成"""
        return html.Div([
            dbc.Spinner([
                html.Div([
                    html.H5("データを処理中です...", className="text-center"),
                    html.P("ファイルを解析してます。しばらくお待ちください。",
                           className="text-center text-muted")
                ])
            ], size="lg", color="primary", type="grow"),
        ], className="text-center", style={'padding': '50px'})

# 使用例とヘルパー関数
def safe_error_display(error_type, error_key, technical_details=None):
    """安全なエラー表示（本番環境では技術的詳細を非表示）"""
    import os

    # 本番環境では技術的詳細を表示しない
    is_production = os.environ.get('FLASK_ENV') == 'production'

    if is_production:
        details = None  # 本番では詳細を隠す
    else:
        details = technical_details  # 開発環境では詳細を表示

    return UserFriendlyMessages.create_error_card(error_type, error_key, details)

def create_upload_help():
    """アップロードヘルプセクション"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("📚 アップロード方法", className="mb-0")
        ]),
        dbc.CardBody([
            html.Ol([
                html.Li("app.pyで生成された分析結果ZIPファイルを用意してください"),
                html.Li("上記のアップロードエリアにファイルをドラッグ&ドロップするか、「ファイルを選択」をクリック"),
                html.Li("ファイルサイズ制限: 100MB以下"),
                html.Li("対応形式: ZIPファイル (.zip) のみ"),
                html.Li("アップロード完了後、各タブで分析結果をご確認ください")
            ]),
            html.Hr(),
            html.P([
                html.Strong("注意: "),
                "このシステムは一時的にデータを処理します。セッション終了後、データは自動的に削除されます。"
            ], className="small text-muted")
        ])
    ], className="mt-3")

if __name__ == "__main__":
    print("ユーザーフレンドリーメッセージシステム")
    print("エラーメッセージ例:")

    messages = UserFriendlyMessages()

    # エラーメッセージの例を表示
    upload_errors = messages.upload_error_messages()
    for key, msg in upload_errors.items():
        print(f"\n{key}:")
        print(f"  タイトル: {msg['title']}")
        print(f"  メッセージ: {msg['message']}")
        print(f"  アイコン: {msg['icon']}")