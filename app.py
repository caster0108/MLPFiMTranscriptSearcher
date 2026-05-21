import streamlit as st
import pandas as pd
import json
import re

# 1. 頁面基本設定
st.set_page_config(page_title="MLP 逐字稿搜尋", layout="wide")
st.title("MLP: FIM 逐字稿搜尋器")

# 2. 讀取資料並合併特定角色
@st.cache_data
def load_data():
    with open('mlp_transcripts_full.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    # 將 A. K. Yarling 合併為 A.K. Yarling
    df['character'] = df['character'].replace('A. K. Yarling', 'A.K. Yarling')
    return df

df = load_data()

# 3. 建立搜尋與篩選介面 (分為兩行排版，讓畫面更寬敞)
st.markdown("### 🔍 搜尋條件")

# 第一行：關鍵字、季別、集數
row1_col1, row1_col2, row1_col3 = st.columns([4, 2, 2])

with row1_col1:
    search_text = st.text_input("輸入台詞關鍵字 (可留空)")

with row1_col2:
    seasons = ["全部"] + sorted(df['season'].unique().tolist())
    selected_season = st.selectbox("選擇季別", seasons)

with row1_col3:
    # 動態連動集數
    if selected_season != "全部":
        ep_list = df[df['season'] == selected_season]['episode_number'].unique().tolist()
    else:
        ep_list = df['episode_number'].unique().tolist()
    episodes = ["全部"] + sorted(ep_list)
    selected_episode = st.selectbox("選擇集數", episodes)

# 第二行：兩種角色搜尋方式並存
row2_col1, row2_col2 = st.columns([4, 4])

with row2_col1:
    # 保留支援複製貼上、反白全選的純文字框
    selected_char_text = st.text_input("自行輸入角色名稱 (支援複製貼上 / 部分名稱)", placeholder="例如: Twilight")

with row2_col2:
    # 加入多選下拉表單，方便瀏覽與點擊
    chars = sorted(df['character'].unique().tolist())
    selected_chars_multi = st.multiselect(
        "或從清單選擇多位角色", 
        options=chars, 
        default=[], 
        placeholder="點擊展開角色清單..."
    )

# 是否標示關鍵字的選項
highlight_keyword = st.checkbox("標示所輸入的關鍵字", value=True)

# 4. 資料過濾邏輯
filtered_df = df.copy()

if search_text:
    filtered_df = filtered_df[filtered_df['dialogue'].str.contains(search_text, case=False, na=False)]

if selected_season != "全部":
    filtered_df = filtered_df[filtered_df['season'] == selected_season]

if selected_episode != "全部":
    filtered_df = filtered_df[filtered_df['episode_number'] == selected_episode]

# 【更新點】合併兩種角色輸入方式的過濾邏輯
char_patterns = []
# 擷取文字框的輸入 (去除前後多餘空白)
if selected_char_text.strip() != "":
    char_patterns.append(re.escape(selected_char_text.strip()))
# 擷取多選表單的輸入
if selected_chars_multi:
    char_patterns.extend([re.escape(c) for c in selected_chars_multi])

# 如果有任何角色條件，將它們組合成正則表達式的 OR 邏輯 (A|B|C)
if char_patterns:
    combined_pattern = '|'.join(char_patterns)
    filtered_df = filtered_df[filtered_df['character'].str.contains(combined_pattern, case=False, na=False)]

# 5. 顯示結果
st.divider() 
st.markdown(f"**共找到 {len(filtered_df)} 筆結果**")
st.markdown("### 🎬 逐字稿對白")

max_display = 100
display_df = filtered_df.head(max_display)

if filtered_df.empty:
    st.info("沒有符合條件的台詞，請嘗試其他關鍵字。")
else:
    if len(filtered_df) > max_display:
        st.warning(f"⚠️ 搜尋結果過多（共 {len(filtered_df)} 筆），目前僅顯示前 {max_display} 筆對白。建議縮小搜尋範圍！")

    for idx, row in display_df.iterrows():
        with st.container():
            st.caption(f"📌 {row['season']} · Ep {row['episode_number']}: {row['episode_title']}")
            
            # 高光標示處理邏輯
            dialogue_text = row['dialogue']
            if search_text and highlight_keyword:
                pattern_kw = re.compile(re.escape(search_text), re.IGNORECASE)
                dialogue_text = pattern_kw.sub(lambda m: f"<mark style='background-color: #ffeb3b; color: black; border-radius: 3px; padding: 0 2px;'>{m.group(0)}</mark>", dialogue_text)
            
            # 對話框呈現 (無頭像)
            with st.chat_message(name=row['character'], avatar=None):
                st.markdown(f"**{row['character']}** : {dialogue_text}", unsafe_allow_html=True)
            
            st.write("")
