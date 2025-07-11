import streamlit as st
import pandas as pd
from scipy.signal import find_peaks
import plotly.graph_objects as go
import random

def read_file(file):
    df = pd.read_csv(file, encoding='shift-jis')
    df = df.loc[:, ['Pulse 1','Pulse 2','Pulse 3','Pulse 4','Pulse 5']].dropna()
    df = df.replace(r'-\s+(\d+)', r'-\1', regex=True).astype('int')
    df['ave'] = df.mean(axis=1)
    return df['ave'].values

def analyze_data(data):
    peaks = find_peaks(data, height=100, distance=20)
    last_index = -10 # 初期値を十分小さくしておく
    zerocross = []
    for i in range(100, len(data) - 1):
        is_zero_cross = False
        if data[i] == 0:
            is_zero_cross = True
        elif data[i] * data[i + 1] < 0:
            is_zero_cross = True
        if is_zero_cross:
            if i - last_index >= 10:
                zerocross.append(i)
                last_index = i
    return peaks[0][:4].tolist(), zerocross[:6]

st.set_page_config(
    page_title="Impulse App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title('インパルス試験結果解析')
with st.sidebar:
    st.header(":blue[結果データ]入力 :sunglasses:", divider=True)
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0

    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []

    files = st.file_uploader(
        "Upload CSV files",
        accept_multiple_files=True,
        type='csv',
        key=st.session_state["file_uploader_key"],
    )

    if files:
        st.session_state["uploaded_files"] = files

    if st.button("Clear uploaded files"):
        st.session_state["file_uploader_key"] += 1
        st.rerun()

    # if files:
    #     st.write("Uploaded files:", st.session_state["uploaded_files"])

    title = st.text_input("Work Serial", "1")
    button = st.button("Run", icon="🔥")

tab01, tab02 = st.tabs(["結果グラフ", "結果テーブル"])
with tab01:
    st.header("結果グラフ :bar_chart:", divider=True)
    df = pd.DataFrame([])
    if button:
        file_num = len(files)
        if file_num == 6:
            figs = []
            for i, file in enumerate(files):
                data = read_file(file)
                peaks, zerocross = analyze_data(data)
                judge = random.choice(['OK', 'NG'])
                res = pd.DataFrame([[title, str(i + 1), judge] + data[peaks].tolist() + zerocross])
                df = pd.concat([df, res])
                # st.write(file.name, peaks, zerocross)
                # Create traces
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[j for j in range(len(data))], y=data,
                            mode='lines',
                            name='result'))
                fig.add_trace(go.Scatter(x=peaks, y=data[peaks],
                            mode='markers', name='peaks'))
                fig.add_trace(go.Scatter(x=zerocross, y=[0] * len(zerocross),
                            mode='markers', name='zero cross'))
                fig.update_layout(
                                title=dict(
                                    text='Results of Impulse Test line no.: ' + str(i + 1)),
                                xaxis=dict(
                                    title=dict(
                                        text='Time [um]'
                                    )
                                ),
                                yaxis=dict(
                                    title=dict(
                                        text='Voltage [V]'
                                    )
                                ),
                        )
                figs.append(fig)
            tabs = st.tabs([str(i + 1) for i in range(6)])
            with tabs[0]:
                st.plotly_chart(figs[0])
            with tabs[1]:
                st.plotly_chart(figs[1])
            with tabs[2]:
                st.plotly_chart(figs[2])
            with tabs[3]:
                st.plotly_chart(figs[3])
            with tabs[4]:
                st.plotly_chart(figs[4])
            with tabs[5]:
                st.plotly_chart(figs[5])
            df.columns = ['シリアル', '素線番号', '判定結果','ピーク1','ピーク2','ピーク3',
                'ピーク4','ゼロクロス点1','ゼロクロス点2','ゼロクロス点3',
                'ゼロクロス点4','ゼロクロス点5','ゼロクロス点6']

with tab02:
    st.header("結果テーブル :neutral_face:", divider=True)
    st.dataframe(df)