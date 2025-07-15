import streamlit as st
import pandas as pd
from scipy.signal import find_peaks
import plotly.graph_objects as go
import random
from streamlit_javascript import st_javascript
import json

pd.options.display.float_format = '{:.1f}'.format

# 定数
PULSE_COLUMNS = ['Pulse 1', 'Pulse 2', 'Pulse 3', 'Pulse 4', 'Pulse 5']
RESULT_COLUMNS = ['シリアル', '素線番号', '判定結果',
                  'ピーク1', 'ピーク2', 'ピーク3', 'ピーク4',
                  'ゼロクロス点1', 'ゼロクロス点2', 'ゼロクロス点3',
                  'ゼロクロス点4', 'ゼロクロス点5', 'ゼロクロス点6']
JUDGMENT_FIELDS = [
    'ピーク1', 'ピーク2', 'ピーク3', 'ピーク4',
    'ゼロクロス点1', 'ゼロクロス点2', 'ゼロクロス点3',
    'ゼロクロス点4', 'ゼロクロス点5', 'ゼロクロス点6'
]

# ファイル読み込みと前処理
def read_file(file):
    df = pd.read_csv(file, encoding='shift-jis')
    df = df[PULSE_COLUMNS].dropna()
    df = df.replace(r'-\s+(\d+)', r'-\1', regex=True).astype(int)
    df['ave'] = df.mean(axis=1)
    return df['ave'].values

# データ解析（ピークとゼロクロス検出）
def analyze_data(data):
    from scipy.signal import find_peaks

    # Detect peaks
    peaks, _ = find_peaks(data, height=100, distance=20)

    # Detect zero-crossings with grouping
    raw_zerocross = []
    last_index = -10
    for i in range(100, len(data) - 1):
        is_zero_cross = data[i] == 0 or (data[i] * data[i + 1] < 0)
        if is_zero_cross and (i - last_index >= 10):
            raw_zerocross.append(i)
            last_index = i

    # Group nearby zero-crossings (within 5 indices) and compute their average
    grouped_zerocross = []
    group = []

    for idx in raw_zerocross:
        if not group:
            group.append(idx)
        elif idx - group[-1] <= 5:
            group.append(idx)
        else:
            avg_idx = int(sum(group) / len(group))
            grouped_zerocross.append(avg_idx * 2)
            group = [idx]

    # Add the last group if exists
    if group:
        avg_idx = int(sum(group) / len(group))
        grouped_zerocross.append(avg_idx * 2)

    return peaks[:4].tolist(), grouped_zerocross[:6]

def judge_result(data_dict, config):
    for key in JUDGMENT_FIELDS:
        settings = config.get(key, {})
        if settings.get('use', False):
            value = data_dict.get(key)
            if value is None or not (settings['min'] <= value <= settings['max']):
                return 'NG'
    return 'OK'

# 判定結果の色付け
def highlight_ok(row):
    return ['background-color: limegreen' if row['判定結果'] == 'OK' else 'background-color: lightcoral' for _ in row]

# グラフ生成
def create_plot(data, peaks, zerocross, line_no):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[i * 2 for i in range(len(data))], y=data, mode='lines', name='result'))
    fig.add_trace(go.Scatter(x=[i * 2 for i in peaks], y=data[peaks], mode='markers', name='peaks', marker={'color':'lightcoral'}))
    fig.add_trace(go.Scatter(x=zerocross, y=[0] * len(zerocross), mode='markers', name='zero cross', marker={'color':'limegreen'}))
    fig.update_layout(
        title=dict(text=f'Results of Impulse Test line no.: {line_no}'),
        xaxis=dict(title=dict(text='Time [um]')),
        yaxis=dict(title=dict(text='Voltage [V]'))
    )
    return fig


# ファイル処理と結果生成
def process_files(files, title):
    df = pd.DataFrame([])
    figs = []
    for i, file in enumerate(files):
        data = read_file(file)
        peaks, zerocross = analyze_data(data)
        # peaks, zerocross を取得した後に判定用データを構築
        data_dict = {}
        for j, key in enumerate(JUDGMENT_FIELDS):
            if j < 4:
                data_dict[key] = data[peaks[j]] if j < len(peaks) else -1
            else:
                idx = j - 4
                data_dict[key] = zerocross[idx] if idx < len(zerocross) else -1

        # 判定実行
        judge = judge_result(data_dict, config)

        # 結果行の構築
        result_row = [title, str(i + 1), judge] + [data_dict.get(k, None) for k in JUDGMENT_FIELDS]
        df = pd.concat([df, pd.DataFrame([result_row])])
        figs.append(create_plot(data, peaks, zerocross, i + 1))
    df = df.reset_index(drop=True)
    df.columns = RESULT_COLUMNS
    return df, figs

# localStorageから設定を取得
config_json = st_javascript("localStorage.getItem('judgment_config');")
config = json.loads(config_json) if config_json else {}

# Streamlit UI
st.set_page_config(page_title="Impulse App", page_icon="🧊", layout="wide", initial_sidebar_state="expanded")
st.title('インパルス試験結果解析')
res_container = st.container()
head = res_container.header('総合判定: ', divider=True)

# サイドバー
with st.sidebar:
    st.header(":blue[結果データ]入力 :sunglasses:", divider=True)
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []

    files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type='csv',
                             key=st.session_state["file_uploader_key"])
    if files:
        st.session_state["uploaded_files"] = files

    if st.button("Clear uploaded files"):
        st.session_state["file_uploader_key"] += 1
        st.rerun()

    title = st.text_input("Work Serial", "1")
    button = st.button("Run", icon="🔥")
    st.page_link("pages/set_config.py", label="判定条件設定", icon="⚙️")

# タブ表示
tab01, tab02 = st.tabs(["結果グラフ", "結果テーブル"])
with tab01:
    st.header("結果グラフ :bar_chart:", divider=True)
    df = pd.DataFrame([])
    if button and len(files):
        df, figs = process_files(files, title)
        tabs = st.tabs([str(i + 1) for i in range(len(files))])
        for i in range(len(files)):
            with tabs[i]:
                st.plotly_chart(figs[i])

with tab02:
    st.header("結果テーブル :1234:", divider=True)
    if not df.empty:
        st.dataframe(df.style.apply(highlight_ok, axis=1))

if len(df):
    if len(df[df['判定結果'] == 'OK'])==len(files):
        head.header('総合判定: OK:heart_eyes_cat:', divider=True)
    else:
        head.header('総合判定: NG:scream_cat:', divider=True)



if config:
    res_container.subheader("現在の判定設定（使用項目のみ）")
    config_table = {
        "項目": [],
        "最小値": [],
        "最大値": []
    }
    for field in JUDGMENT_FIELDS:
        settings = config.get(field, {})
        if settings.get("use", False):  # 使用する項目のみ表示
            config_table["項目"].append(field)
            config_table["最小値"].append(settings.get("min", ""))
            config_table["最大値"].append(settings.get("max", ""))
    res_container.table(config_table)

