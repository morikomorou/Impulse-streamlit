import streamlit as st
from streamlit_javascript import st_javascript
import json

# 判定項目リスト
JUDGMENT_FIELDS = [
    'ピーク1', 'ピーク2', 'ピーク3', 'ピーク4',
    'ゼロクロス点1', 'ゼロクロス点2', 'ゼロクロス点3',
    'ゼロクロス点4', 'ゼロクロス点5', 'ゼロクロス点6'
]

# ローカルストレージキー
LOCAL_STORAGE_KEY = "judgment_config"

# ページ設定
st.set_page_config(page_title="判定条件設定", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")
st.title("判定条件設定 ⚙️")

# サイドバー
with st.sidebar:
    st.page_link("analyze_once.py", label="ホーム", icon="🏠")

# ローカルストレージから設定を取得
config_json = st_javascript("localStorage.getItem('judgment_config');")
config = json.loads(config_json) if config_json else {}

# 入力フォーム
new_config = {}
with st.form("judgment_form"):
    st.write("各項目について、判定に使用するかどうかと、使用する場合の最小値・最大値を設定してください。")
    invalid_fields = []
    for field in JUDGMENT_FIELDS:
        col1, col2, col3 = st.columns([2, 3, 3])
        with col1:
            use_field = st.checkbox(f"{field} を使用", value=config.get(field, {}).get("use", False), key=f"{field}_use")
        with col2:
            min_val = st.number_input(f"{field} の最小値", value=config.get(field, {}).get("min", 0.0), key=f"{field}_min", step=0.5)
        with col3:
            max_val = st.number_input(f"{field} の最大値", value=config.get(field, {}).get("max", 1000.0), key=f"{field}_max", step=0.5)
        new_config[field] = {"use": use_field, "min": min_val, "max": max_val}
        if use_field and min_val > max_val:
            invalid_fields.append(field)
    submitted = st.form_submit_button("保存")
    if submitted:
        if invalid_fields:
            st.warning(f"以下の項目で最小値が最大値を超えています: {', '.join(invalid_fields)}。修正してください。")
        else:
            config_str = json.dumps(new_config)
            st_javascript(f"localStorage.setItem('{LOCAL_STORAGE_KEY}', `{config_str}`);")
            st.success("設定を保存しました。次回も自動的に読み込まれます。")
