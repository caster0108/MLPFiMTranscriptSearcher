import streamlit as st
import pandas as pd
import json

# 1. 頁面基本設定
st.set_page_config(page_title="MLP 逐字稿搜尋", page_icon="🦄", layout="wide")
st.title("🦄 MLP: FIM 逐字稿搜尋器")

# 2. 讀取資料 (加上快取裝飾器)
@st.cache_data
def load_data():
    # 讀取剛剛爬蟲抓下來的完整 JSON
    with open('mlp_transcripts_full.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 轉換為 Pandas 的 DataFrame，方便後續做表格處理與過濾
    return pd.DataFrame(data)

df = load_data()

# 3. 建立搜尋與篩選介面 (切分成三個欄位)
st.markdown("### 🔍 搜尋條件")
col1, col2, col3 = st.columns(3)

with col1:
    search_text = st.text_input("輸入台詞關鍵字 (可留空)")
with col2:
    # 提取所有季別並加上 "All" 選項
    seasons = ["All"] + sorted(df['season'].unique().tolist())
    selected_season = st.selectbox("選擇季別", seasons)
with col3:
    # 提取所有角色並排序
    chars = ["All"] + sorted(df['character'].unique().tolist())
    selected_char = st.selectbox("選擇角色", chars)

# 4. 資料過濾邏輯
filtered_df = df.copy()

if search_text:
    # case=False 代表不分大小寫，na=False 避免遇到空值報錯
    filtered_df = filtered_df[filtered_df['dialogue'].str.contains(search_text, case=False, na=False)]

if selected_season != "All":
    filtered_df = filtered_df[filtered_df['season'] == selected_season]

if selected_char != "All":
    # 使用 contains 可以做到「包含該角色」的搜尋 (例如選 Applejack 會帶出 Applejack and Rarity)
    filtered_df = filtered_df[filtered_df['character'].str.contains(selected_char, case=False, na=False)]

# 5. 顯示結果與匯出區塊
st.divider() # 畫一條分隔線

# 計算結果數量並建立匯出按鈕的並排版面
result_col, csv_col, json_col = st.columns([6, 1, 1])

with result_col:
    st.markdown(f"**共找到 {len(filtered_df)} 筆結果**")

with csv_col:
    st.download_button(
        label="📥 匯出 CSV",
        data=filtered_df.to_csv(index=False).encode('utf-8-sig'), # utf-8-sig 內建 BOM，Excel 打開不會亂碼
        file_name="mlp_transcripts.csv",
        mime="text/csv",
        use_container_width=True
    )

with json_col:
    st.download_button(
        label="📥 匯出 JSON",
        data=filtered_df.to_json(orient="records", force_ascii=False, indent=2),
        file_name="mlp_transcripts.json",
        mime="application/json",
        use_container_width=True
    )

# 6. 顯示互動式資料表
# use_container_width=True 會讓表格自動填滿畫面寬度
# 6. 顯示結果（改為劇本/對話樣式呈現）
st.markdown("### 🎬 逐字稿對白")

# 限制畫面上最多只渲染前 100 筆，避免瀏覽器卡死
max_display = 100
display_df = filtered_df.head(max_display)

if filtered_df.empty:
    st.info("沒有符合條件的台詞，請嘗試其他關鍵字。")
else:
    # 如果總數超過 100 筆，給予提示
    if len(filtered_df) > max_display:
        st.warning(f"⚠️ 搜尋結果過多（共 {len(filtered_df)} 筆），目前僅顯示前 {max_display} 筆對白。建議縮小搜尋範圍！")

    # 用迴圈把每一行台詞像劇本一樣印出來
    for idx, row in display_df.iterrows():
        # 建立一個容器，讓每一筆對白維持獨立區塊
        with st.container():
            # 印出集數標題小標籤
            st.caption(f"📌 {row['season']} · {row['episode_title']}")
            
            # 使用 Streamlit 內建的聊天訊息泡泡樣式
            # 這裡的 avatar 可以放 emoji（例如獨角獸），讓介面看起來更有活力
            with st.chat_message(name=row['character'], avatar="🦄"):
                st.markdown(f"**{row['character']}** : {row['dialogue']}")
            
            # 每條對白之間畫一條淡淡的分隔線
            st.write("")
