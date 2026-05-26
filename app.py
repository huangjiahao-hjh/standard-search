#!/usr/bin/env python3
"""
全国标准信息检索平台 - 可视化 Web 应用 (Streamlit)
"""

import streamlit as st
import pandas as pd
import time
from scraper import (
    fetch_tc_committees,
    iter_tc_results,
    iter_keyword_results,
    CATEGORY_CONFIG,
    ALL_FIELDS,
)

# ── 页面配置 ──────────────────────────────────────────
st.set_page_config(
    page_title="全国标准信息检索平台",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 样式 ────────────────────────────────────────────
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * {font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;}
    .stApp {background: linear-gradient(135deg, #f0f4f8 0%, #e8edf5 100%);}
    .stApp header {display: none;}

    ::-webkit-scrollbar {width: 6px; height: 6px;}
    ::-webkit-scrollbar-track {background: transparent;}
    ::-webkit-scrollbar-thumb {background: #c1c9d6; border-radius: 3px;}
    ::-webkit-scrollbar-thumb:hover {background: #a0aab8;}

    .main-container {max-width: 1400px; margin: 0 auto; padding: 0 0.5rem;}

    .hero {
        background: linear-gradient(135deg, #0f2b5c 0%, #1a4a8a 40%, #2563eb 70%, #3b82f6 100%);
        border-radius: 20px; padding: 2.2rem 2.8rem; margin-bottom: 2rem;
        color: white; position: relative; overflow: hidden;
        box-shadow: 0 8px 32px rgba(37, 99, 235, 0.25);
    }
    .hero::before {
        content: ''; position: absolute; top: -50%; right: -20%;
        width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero::after {
        content: ''; position: absolute; bottom: -30%; left: 10%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero table {position: relative; z-index: 1;}
    .hero h1 {
        font-size: 2rem; font-weight: 800; margin: 0 0 0.3rem 0; letter-spacing: 1.5px;
        background: linear-gradient(90deg, #fff, #bfd8ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero p {font-size: 0.95rem; margin: 0; opacity: 0.8; font-weight: 300; color: #e0e8ff;}
    .hero-icon {
        font-size: 2.8rem; line-height: 1; display: block; text-align: center;
        filter: drop-shadow(0 2px 8px rgba(255,255,255,0.2));
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%);
        border-right: 1px solid #e5e9f0; padding-top: 1rem;
    }
    [data-testid="stSidebar"] .sidebar-title {
        font-size: 1.15rem; font-weight: 700; color: #0f2b5c;
        padding: 0.8rem 0.5rem; display: flex; align-items: center; gap: 0.5rem;
        border-bottom: 2px solid #eef3fc; margin-bottom: 0.5rem;
    }
    [data-testid="stSidebar"] .stRadio > div {gap: 0.2rem;}
    [data-testid="stSidebar"] .stRadio label {
        padding: 0.6rem 1rem; border-radius: 10px; transition: all 0.2s;
        font-weight: 500; color: #4b5563;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(37, 99, 235, 0.06); color: #1a4a8a;
    }
    [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {font-size: 0.9rem;}

    .card {
        background: rgba(255,255,255,0.95); backdrop-filter: blur(10px);
        border-radius: 16px; padding: 1.8rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.03);
        border: 1px solid rgba(255,255,255,0.8); margin-bottom: 1.2rem;
        transition: box-shadow 0.2s;
    }
    .card:hover {box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.06);}
    .card-title {
        font-size: 1.1rem; font-weight: 700; color: #0f2b5c;
        margin-bottom: 1.2rem; display: flex; align-items: center; gap: 0.5rem;
        letter-spacing: 0.3px;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a4a8a, #2563eb);
        border: none; color: white; font-weight: 600; height: 2.8rem; border-radius: 10px;
        transition: all 0.25s;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
        letter-spacing: 0.5px; font-size: 0.9rem;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
    }
    div.stButton > button[kind="primary"]:active {transform: translateY(0);}

    .stat-card {
        background: linear-gradient(135deg, #ffffff, #f8faff);
        border-radius: 14px; padding: 1.3rem 1rem; text-align: center;
        border: 1px solid #eef0f4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: all 0.25s; position: relative; overflow: hidden;
    }
    .stat-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #2563eb, #60a5fa);
        opacity: 0; transition: opacity 0.25s;
    }
    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }
    .stat-card:hover::before {opacity: 1;}
    .stat-card .num {
        font-size: 1.8rem; font-weight: 800;
        background: linear-gradient(135deg, #1a4a8a, #2563eb);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; line-height: 1.2;
    }
    .stat-card .label {font-size: 0.8rem; font-weight: 500; color: #6b7280; margin-top: 0.3rem;}
    .stat-card .sublabel {font-size: 0.7rem; color: #9ca3af; margin-top: 0.2rem;}

    [data-testid="stDataFrame"] {
        border-radius: 12px; border: 1px solid #eef0f4;
        overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    [data-testid="stDataFrame"] thead tr th {
        background: #f8faff !important; font-weight: 600 !important;
        color: #1e293b !important; font-size: 0.8rem !important;
        text-transform: uppercase; letter-spacing: 0.5px;
        padding: 0.75rem 1rem !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover td {background: #f0f5ff !important;}

    .streamlit-expanderHeader {font-weight: 600; color: #1e293b; border-radius: 8px;}

    .footer {
        text-align: center; padding: 2rem 0 0.5rem 0;
        color: #b0b8c4; font-size: 0.7rem; line-height: 1.8;
        border-top: 1px solid #eef0f4; margin-top: 2.5rem;
    }
    .footer a {color: #94a3b8; text-decoration: none; transition: color 0.2s;}
    .footer a:hover {color: #2563eb;}

    div.stProgress > div > div > div > div {
        background: linear-gradient(90deg, #2563eb, #60a5fa, #93c5fd);
        background-size: 200% 100%;
        animation: shimmer 1.5s ease-in-out infinite;
    }
    @keyframes shimmer {
        0%, 100% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
    }

    div[data-testid="stNumberInput"] label {font-size: 0.85rem; color: #475569; font-weight: 500;}
    div[data-testid="stNumberInput"] input {border-radius: 8px;}

    div[data-testid="stTextInput"] input {
        border-radius: 10px; border: 1px solid #e2e8f0;
        padding: 0.6rem 1rem; font-size: 0.95rem;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    div[data-testid="stMultiSelect"] > div > div {border-radius: 10px; border-color: #e2e8f0;}

    .stAlert {border-radius: 12px; border: none; box-shadow: 0 1px 3px rgba(0,0,0,0.03);}

    div.stDownloadButton > button {
        border-radius: 10px; font-weight: 500; transition: all 0.2s;
    }
    div.stDownloadButton > button:hover {transform: translateY(-1px);}

    .stCaption {color: #6b7280; font-size: 0.8rem;}

    .stSpinner > div {border-color: #2563eb !important;}
</style>""",
    unsafe_allow_html=True,
)

# ── Session 状态初始化 ────────────────────────────────
if "tc_loaded" not in st.session_state:
    st.session_state.tc_loaded = False
    st.session_state.tc_committees = []
    st.session_state.tc_dict = {}
if "search_results" not in st.session_state:
    st.session_state.search_results = None
    st.session_state.search_summary = ""


# ── 缓存 TC 列表 ─────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="正在加载 TC 列表...")
def load_tc_committees():
    committees = fetch_tc_committees()
    return committees, {c["name"]: c["code"] for c in committees}


# ── 统计卡片 ──────────────────────────────────────────
def show_stats(df):
    cols = st.columns(4)
    with cols[0]:
        st.markdown(
            f'<div class="stat-card"><div class="num">{len(df)}</div>'
            f'<div class="label">总条数</div></div>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        cats = df["category"].value_counts()
        cat_names = {k: v["name"] for k, v in CATEGORY_CONFIG.items()}
        label = " · ".join(
            f"{cat_names.get(k, k)} {v}" for k, v in cats.head(3).items()
        )
        st.markdown(
            f'<div class="stat-card"><div class="num">{len(cats)}</div>'
            f'<div class="label">标准类别</div>'
            f'<div class="sublabel">{label}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[2]:
        states = df["state"].value_counts()
        label = " · ".join(f"{k} {v}" for k, v in states.head(3).items())
        st.markdown(
            f'<div class="stat-card"><div class="num">{len(states)}</div>'
            f'<div class="label">实施状态</div>'
            f'<div class="sublabel">{label}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[3]:
        if "tc_code" in df.columns and df["tc_code"].str.len().sum() > 0:
            tcs = df["tc_code"].value_counts()
            valid = tcs[tcs.index != ""]
            label = " · ".join(f"{k}" for k in valid.head(3).index)
            st.markdown(
                f'<div class="stat-card"><div class="num">{len(valid)}</div>'
                f'<div class="label">关联 TC</div>'
                f'<div class="sublabel">{label}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="stat-card"><div class="num">—</div>'
                '<div class="label">关联 TC</div></div>',
                unsafe_allow_html=True,
            )


# ── Footer ────────────────────────────────────────────
FOOTER_HTML = """
<div class="footer">
    注：本平台仅用于标准信息查询与学习研究，请勿恶意爬取或攻击。<br>
    作者：JiaHao Huang ｜ 联系邮箱：
    <a href="mailto:huakaiquwan@gmail.com">huakaiquwan@gmail.com</a>
</div>
"""


def show_footer():
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)


# ── 结果数据框 + 下载 ───────────────────────────────
def show_results(df, filename_base):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card-title">📊 检索结果（共 {len(df)} 条）</div>',
        unsafe_allow_html=True,
    )

    # 内联筛选
    with st.expander("🔍 筛选结果", expanded=False):
        filter_cols = st.columns(4)
        filters = {}
        for i, col_name in enumerate(
            ["standard_code", "standard_name", "state", "charge_dept"]
        ):
            if col_name in df.columns and df[col_name].nunique() > 1:
                vals = [""] + sorted(df[col_name].dropna().unique().tolist())
                filters[col_name] = filter_cols[i % 4].selectbox(
                    col_name, vals, key=f"filter_{col_name}"
                )

    filtered = df.copy()
    for col_name, val in filters.items():
        if val:
            filtered = filtered[filtered[col_name] == val]

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.caption(f"当前筛选后: {len(filtered)} 条")
    with col_right:
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        now = time.strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 下载 CSV",
            csv,
            f"{filename_base}_{now}.csv",
            "text/csv",
        )

    st.dataframe(filtered, width="stretch", height=500)

    with st.expander("📈 统计概览"):
        show_stats(filtered)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  侧边栏导航
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">📋 标准检索平台</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    mode = st.radio(
        "选择功能",
        ["🔑 关键词检索", "🏷️ TC 标委会检索", "📋 TC 标委会列表"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("数据来源：全国标准信息公共服务平台")

# ══════════════════════════════════════════════════════
#  主界面
# ══════════════════════════════════════════════════════

st.markdown('<div class="main-container">', unsafe_allow_html=True)

# ── 顶部横幅 ──
st.markdown(
    """
<div class="hero">
    <table width="100%"><tr>
        <td width="50"><span class="hero-icon">📋</span></td>
        <td>
            <h1>全国标准信息检索平台</h1>
            <p>从全国标准信息公共服务平台检索标准数据，支持关键词检索和 TC 标委会检索</p>
        </td>
    </tr></table>
</div>
""",
    unsafe_allow_html=True,
)


# ── 模式 1：关键词检索 ─────────────────────────────
if "关键词" in mode:
    st.markdown(
        '<div class="card"><div class="card-title">🔑 关键词检索</div>',
        unsafe_allow_html=True,
    )

    col_kw, col_cat = st.columns([2, 1])
    with col_kw:
        keyword = st.text_input(
            "关键词",
            placeholder="例如：光伏、消防、人工智能...",
            label_visibility="collapsed",
        )
    with col_cat:
        categories = st.multiselect(
            "标准类别",
            options=list(CATEGORY_CONFIG.keys()),
            default=["national"],
            format_func=lambda x: CATEGORY_CONFIG[x]["name"],
            help="可多选",
        )

    col_ps, col_mp, col_btn = st.columns([1, 1, 1])
    with col_ps:
        page_size = st.number_input(
            "每页条数", min_value=5, max_value=100, value=15, step=5
        )
    with col_mp:
        max_pages = st.number_input(
            "最大页数（0=不限）",
            min_value=0, max_value=200, value=0, step=1,
            help="限制抓取页数以节省时间",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button("🚀 开始检索", type="primary", width="stretch")

    st.markdown("</div>", unsafe_allow_html=True)

    if search_clicked:
        if not keyword.strip():
            st.warning("请输入关键词")
            st.stop()
        if not categories:
            st.warning("请选择至少一个标准类别")
            st.stop()

        results = []
        bar = st.progress(0, text="准备中...")
        status = st.empty()

        for i, cat in enumerate(categories):
            name = CATEGORY_CONFIG[cat]["name"]
            status.info(f"正在检索 {name}...")
            count = 0
            for row in iter_keyword_results(cat, keyword.strip(), page_size=page_size, max_pages=max_pages):
                results.append(row)
                count += 1
            bar.progress((i + 1) / len(categories), text=f"已完成 {name}（{count} 条）")
            time.sleep(0.3)

        bar.empty()
        status.empty()

        if results:
            df = pd.DataFrame(results)
            st.session_state.search_results = df
            st.session_state.search_summary = f"关键词「{keyword}」"
            show_results(df, keyword.strip())
        else:
            st.warning("未找到匹配结果，请尝试其他关键词或类别。")

    elif st.session_state.search_results is not None:
        st.info(
            f"上次检索结果：{st.session_state.search_summary}，"
            f"共 {len(st.session_state.search_results)} 条"
        )
        if st.button("📂 显示上次结果"):
            show_results(
                st.session_state.search_results,
                st.session_state.search_summary.replace(" ", "_"),
            )


# ── 模式 2：TC 标委会检索 ──────────────────────────
elif "TC 标委会检索" in mode:
    st.markdown(
        '<div class="card"><div class="card-title">🏷️ TC 标委会检索</div>',
        unsafe_allow_html=True,
    )

    committees, tc_dict = load_tc_committees()

    if not committees:
        st.error("无法获取 TC 列表，请检查网络连接后刷新页面。")
        st.stop()

    tc_names = list(tc_dict.keys())
    selected_names = st.multiselect(
        "选择 TC 标委会",
        options=tc_names,
        placeholder="输入名称搜索...",
        help="可搜索并多选",
    )

    col_ps2, col_btn2 = st.columns([1, 1])
    with col_ps2:
        page_size = st.number_input(
            "每页条数",
            min_value=5, max_value=100, value=50, step=5,
            key="tc_page_size",
        )
    with col_btn2:
        st.markdown("<br>", unsafe_allow_html=True)
        tc_search_clicked = st.button("🚀 开始检索", type="primary", width="stretch")

    st.markdown("</div>", unsafe_allow_html=True)

    if tc_search_clicked:
        if not selected_names:
            st.warning("请选择至少一个 TC 标委会")
            st.stop()

        results = []
        bar = st.progress(0, text="准备中...")
        status = st.empty()

        for i, name in enumerate(selected_names):
            code = tc_dict[name]
            status.info(f"正在检索 {name}（{code}）...")
            count = 0
            for row in iter_tc_results(code, page_size=page_size):
                results.append(row)
                count += 1
            bar.progress(
                (i + 1) / len(selected_names),
                text=f"已完成 {name}（{count} 条）",
            )
            time.sleep(0.3)

        bar.empty()
        status.empty()

        if results:
            df = pd.DataFrame(results)
            short = "_".join(selected_names[:2]).replace(" ", "")[:50]
            show_results(df, short)
        else:
            st.warning("未找到匹配结果。")


# ── 模式 3：TC 标委会列表 ──────────────────────────
elif "TC 标委会列表" in mode:
    st.markdown(
        '<div class="card"><div class="card-title">📋 TC 标委会列表</div>',
        unsafe_allow_html=True,
    )

    committees, tc_dict = load_tc_committees()

    if not committees:
        st.error("无法获取 TC 列表，请检查网络连接。")
    else:
        df_tc = pd.DataFrame(committees)

        search_tc = st.text_input(
            "🔍 搜索 TC 名称或编号",
            placeholder="输入关键字过滤...",
        )
        if search_tc:
            mask = df_tc["name"].str.contains(search_tc, case=False, na=False)
            df_tc = df_tc[mask]

        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.caption(f"共 {len(committees)} 个标委会，当前筛选 {len(df_tc)} 个")
        with col_b:
            csv_tc = df_tc.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 下载列表", csv_tc, "tc_list.csv", "text/csv")

        st.dataframe(
            df_tc,
            width="stretch",
            height=600,
            column_config={
                "code": st.column_config.TextColumn("编号", width="small"),
                "name": st.column_config.TextColumn("名称", width="large"),
            },
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ── Footer ──────────────────────────────────────────
show_footer()
st.markdown("</div>", unsafe_allow_html=True)
