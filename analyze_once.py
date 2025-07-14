import streamlit as st
import pandas as pd
from scipy.signal import find_peaks
import plotly.graph_objects as go
import random

# 定数
PULSE_COLUMNS = ['Pulse 1', 'Pulse 2', 'Pulse 3', 'Pulse 4', 'Pulse 5']
RESULT_COLUMNS = ['シリアル', '素線番号', '判定結果',
                  'ピーク1', 'ピーク2', 'ピーク3', 'ピーク4',
                  'ゼロクロス点1', 'ゼロクロス点2', 'ゼロクロス点3',
                  'ゼロクロス点4', 'ゼロクロス点5', 'ゼロクロス点6']

# ファイル読み込みと前処理
def read_file(file):
    df = pd.read_csv(file, encoding='shift-jis')
    df = df[PULSE_COLUMNS].dropna()
    df = df.replace(r'-\s+(\d+)', r'-\1', regex=True).astype(int)
    df['ave'] = df.mean(axis=1)
    return df['ave'].values

# データ解析（ピークとゼロクロス検出）
def analyze_data(data):
    peaks, _ = find_peaks(data, height=100, distance=20)
    zerocross = []
    last_index = -10
    for i in range(100, len(data) - 1):
        is_zero_cross = data[i] == 0 or (data[i] * data[i + 1] < 0)
        if is_zero_cross and (i - last_index >= 10):
            zerocross.append(i)
            last_index = i
    return peaks[:4].tolist(), zerocross[:6]

# 判定結果の色付け
def highlight_ok(row):
    return ['background-color: limegreen' if row['判定結果'] == 'OK' else 'background-color: lightcoral' for _ in row]

# グラフ生成
def create_plot(data, peaks, zerocross, line_no):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(data))), y=data, mode='lines', name='result'))
    fig.add_trace(go.Scatter(x=peaks, y=data[peaks], mode='markers', name='peaks', marker={'color':'lightcoral'}))
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
        judge = random.choice(['OK', 'NG'])
        result_row = [title, str(i + 1), judge] + data[peaks].tolist() + zerocross
        df = pd.concat([df, pd.DataFrame([result_row])])
        figs.append(create_plot(data, peaks, zerocross, i + 1))
    df = df.reset_index(drop=True)
    df.columns = RESULT_COLUMNS
    return df, figs

# Streamlit UI
st.set_page_config(page_title="Impulse App", page_icon="🧊", layout="wide", initial_sidebar_state="expanded")
st.title('インパルス試験結果解析')
res_container = st.container()
res_container.header('総合判定: ', divider=True)

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

# タブ表示
tab01, tab02 = st.tabs(["結果グラフ", "結果テーブル"])
with tab01:
    st.header("結果グラフ :bar_chart:", divider=True)
    df = pd.DataFrame([])
    if button and len(files) == 6:
        df, figs = process_files(files, title)
        tabs = st.tabs([str(i + 1) for i in range(6)])
        for i in range(6):
            with tabs[i]:
                st.plotly_chart(figs[i])

with tab02:
    st.header("結果テーブル :neutral_face:", divider=True)
    if not df.empty:
        st.dataframe(df.style.apply(highlight_ok, axis=1))

if len(df):
    if len(df[df['判定結果'] == 'OK'])==6:
        res_container.write('OK(ランダムに判定チュウ:rat:)')
    else:
        res_container.write('NG(ランダムに判定チュウ:rat:)')