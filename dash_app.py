import base64
import io
import zipfile

import dash
import pandas as pd
from dash import Input, Output, dcc, html

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        dcc.Store(id="analysis-data-store"),
        html.H1("Shift-Suite 高速分析ビューア"),
        dcc.Upload(
            id="upload-zip",
            children=html.Div(
                [
                    "分析結果のZIPファイルをここにドラッグ＆ドロップ、または ",
                    html.A("ファイルを選択"),
                ]
            ),
            style={
                "width": "90%",
                "height": "200px",
                "lineHeight": "200px",
                "borderWidth": "2px",
                "borderDash": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "20px auto",
            },
        ),
        html.Div(id="dashboard-container"),
    ]
)


@app.callback(Output("analysis-data-store", "data"), Input("upload-zip", "contents"))
def load_zip(contents):
    if contents is None:
        return {}
    try:
        _, b64data = contents.split(",", 1)
        decoded = base64.b64decode(b64data)
    except Exception:
        return {}

    data = {}
    with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
        for name in zf.namelist():
            if name.endswith(".parquet"):
                with zf.open(name) as f:
                    df = pd.read_parquet(f)
                data[name] = df.to_json()
            elif name.endswith(".csv"):
                with zf.open(name) as f:
                    df = pd.read_csv(f)
                data[name] = df.to_json()
    return data


@app.callback(Output("dashboard-container", "children"), Input("analysis-data-store", "data"))
def update_dashboard(data):
    if not data:
        return html.Div(
            "分析結果ZIPをアップロードしてください", style={"textAlign": "center"}
        )

    children = [html.H2("概要"), html.Ul([html.Li(k) for k in data.keys()])]
    return children


if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
