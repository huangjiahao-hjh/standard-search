#!/usr/bin/env python3
"""
全国标准信息检索平台 - 可视化 Web 应用 (Streamlit)
"""

import io
import time
from typing import Dict

import pandas as pd
import streamlit as st
from scraper import (
    CATEGORY_CONFIG,
    fetch_tc_committees,
    get_search_total,
    get_tc_search_total,
    iter_keyword_results,
    iter_tc_results,
)

# ── 页面配置 ──────────────────────────────────────────
st.set_page_config(
    page_title="全国标准信息检索平台",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 中文表头映射 ──────────────────────────────────────
COLUMN_LABELS: Dict[str, str] = {
    "keyword": "关键词",
    "category": "标准类别",
    "standard_code": "标准号",
    "standard_name": "标准名称",
    "standard_nature": "标准性质",
    "charge_dept": "主管部门",
    "guikou_unit": "归口单位",
    "drafting_units": "起草单位",
    "issue_date": "发布日期",
    "act_date": "实施日期",
    "state": "实施状态",
    "tc_code": "TC编号",
    "draft_staff": "起草人",
    "ics": "ICS分类号",
}
CAT_NAME_MAP = {k: v["name"] for k, v in CATEGORY_CONFIG.items()}


def rename_cols(df: pd.DataFrame) -> pd.DataFrame:
    """将英文列名映射为中文。"""
    return df.rename(columns=COLUMN_LABELS)


# ── 样式 (Apple 风格) ────────────────────────────────
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── 全局 ── */
    .stApp {background: #f5f5f7;}
    .stApp header {display: none;}

    ::-webkit-scrollbar {width: 5px; height: 5px;}
    ::-webkit-scrollbar-track {background: transparent;}
    ::-webkit-scrollbar-thumb {background: #c7c7cc; border-radius: 3px;}

    .main-container {max-width: 1400px; margin: 0 auto; padding: 0 0.5rem;}

    /* ── 顶部横幅 ── */
    .hero {
        background: linear-gradient(135deg, #e8ecf4 0%, #f0f4fa 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.8rem;
        border: 1px solid rgba(255,255,255,0.8);
    }
    .hero h1 {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        font-size: 1.8rem; font-weight: 700;
        margin: 0 0 0.2rem 0;
        color: #1d1d1f;
        letter-spacing: -0.5px;
    }
    .hero p {
        font-size: 0.9rem; margin: 0;
        color: #86868b;
        font-weight: 400;
    }
    .hero-icon {
        font-size: 2.4rem; line-height: 1;
        display: block; text-align: center;
    }

    /* ── 侧边栏 - 毛玻璃效果 ── */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.72);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(0,0,0,0.06);
    }
    [data-testid="stSidebar"] .sidebar-title {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        font-size: 1.1rem; font-weight: 600;
        color: #1d1d1f;
        padding: 0.6rem 0.5rem 0.8rem;
        display: flex; align-items: center; gap: 0.5rem;
        border-bottom: 1px solid rgba(0,0,0,0.05);
    }
    /* 隐藏侧边栏折叠按钮 */
    button[data-testid="baseButton-sidebarCollapse"] {display: none !important;}
    section[data-testid="stSidebar"] > div:first-child {width: 100%;}
    /* 侧边栏 radio 风格 */
    [data-testid="stSidebar"] .stRadio > div {gap: 0.15rem;}
    [data-testid="stSidebar"] .stRadio label {
        padding: 0.55rem 1rem; border-radius: 8px;
        transition: all 0.15s;
        font-size: 0.88rem; font-weight: 500; color: #3a3a3c;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(0,122,255,0.07);
        color: #007AFF;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
        display: none;
    }
    [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
        font-size: 0.88rem;
    }

    /* ── 卡片 ── */
    .card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.5rem 1.8rem;
        border: none;
        box-shadow: 0 0 0 1px rgba(0,0,0,0.03), 0 2px 4px rgba(0,0,0,0.04);
        margin-bottom: 1.2rem;
    }
    .card-title {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        font-size: 1.05rem; font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 1.2rem;
        display: flex; align-items: center; gap: 0.5rem;
        letter-spacing: -0.3px;
    }

    /* ── 主操作按钮 ── */
    div.stButton > button[kind="primary"] {
        background: #007AFF;
        border: none;
        color: white;
        font-weight: 500;
        height: 2.6rem;
        border-radius: 8px;
        transition: all 0.15s;
        font-size: 0.9rem;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #0066d6;
        box-shadow: 0 2px 8px rgba(0,122,255,0.3);
    }
    div.stButton > button[kind="primary"]:active {
        transform: scale(0.97);
    }

    /* ── 统计卡片 ── */
    .stat-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.2rem 0.8rem;
        text-align: center;
        box-shadow: 0 0 0 1px rgba(0,0,0,0.03), 0 1px 3px rgba(0,0,0,0.03);
        transition: all 0.2s;
    }
    .stat-card:hover {
        box-shadow: 0 0 0 1px rgba(0,0,0,0.03), 0 4px 12px rgba(0,0,0,0.06);
        transform: translateY(-1px);
    }
    .stat-card .num {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        font-size: 1.7rem; font-weight: 700;
        color: #007AFF;
        line-height: 1.2;
    }
    .stat-card .label {
        font-size: 0.78rem; font-weight: 500;
        color: #8e8e93; margin-top: 0.2rem;
    }
    .stat-card .sublabel {
        font-size: 0.68rem; color: #aeaeb2; margin-top: 0.15rem;
    }

    /* ── 数据表格 ── */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.06);
        overflow: hidden;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    [data-testid="stDataFrame"] thead tr th {
        background: #fafafa !important;
        font-weight: 600 !important;
        color: #1d1d1f !important;
        font-size: 0.78rem !important;
        padding: 0.6rem 1rem !important;
        border-bottom: 1px solid #e5e5ea !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover td {background: #f2f2f7 !important;}
    [data-testid="stDataFrame"] tbody td {
        font-size: 0.85rem;
        padding: 0.5rem 1rem !important;
        border-bottom: 1px solid #f0f0f0 !important;
    }

    /* ── expander ── */
    .streamlit-expanderHeader {
        font-weight: 500; color: #1d1d1f;
        border-radius: 8px;
        background: #fafafa;
    }

    /* ── Footer ── */
    .footer {
        text-align: center; padding: 2rem 0 0.5rem 0;
        color: #aeaeb2; font-size: 0.68rem; line-height: 1.8;
        border-top: 1px solid rgba(0,0,0,0.05);
        margin-top: 2.5rem;
    }
    .footer a {color: #8e8e93; text-decoration: none; transition: color 0.15s;}
    .footer a:hover {color: #007AFF;}

    /* ── 进度条 ── */
    div.stProgress > div > div > div > div {
        background: linear-gradient(90deg, #007AFF, #34a853);
        border-radius: 4px;
    }

    /* ── 输入框 ── */
    div[data-testid="stTextInput"] input {
        border-radius: 8px;
        border: 1px solid #d1d1d6;
        padding: 0.5rem 0.8rem;
        font-size: 0.9rem;
        transition: border-color 0.15s;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #007AFF;
        box-shadow: 0 0 0 3px rgba(0,122,255,0.12);
    }

    div[data-testid="stNumberInput"] label {font-size: 0.82rem; color: #3a3a3c; font-weight: 500;}
    div[data-testid="stNumberInput"] input {border-radius: 8px;}

    div[data-testid="stMultiSelect"] > div > div {border-radius: 8px; border-color: #d1d1d6;}

    .stAlert {border-radius: 10px; border: none;}

    div.stDownloadButton > button {
        border-radius: 8px; font-weight: 500;
        transition: all 0.15s;
        border: 1px solid #d1d1d6;
    }
    div.stDownloadButton > button:hover {
        border-color: #007AFF;
        color: #007AFF;
    }

    .stCaption {color: #8e8e93; font-size: 0.78rem;}
</style>""",
    unsafe_allow_html=True,
)

# ── Session 状态 ─────────────────────────────────────
if "tc_dict" not in st.session_state:
    st.session_state.tc_dict = {}
if "search_results" not in st.session_state:
    st.session_state.search_results = None
    st.session_state.search_by_category = {}
    st.session_state.search_summary = ""


# ── 缓存 TC 列表 ─────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="正在加载 TC 列表...")
def load_tc_committees():
    committees = fetch_tc_committees()
    return committees, {c["name"]: c["code"] for c in committees}


# ── 多 Sheet Excel 导出 ─────────────────────────────
def make_multisheet_excel(sheet_dict: Dict[str, pd.DataFrame]) -> bytes:
    """生成多 Sheet Excel 文件的 bytes。"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheet_dict.items():
            # Excel sheet name 不能超 31 字符
            safe_name = sheet_name[:31]
            df_renamed = rename_cols(df)
            df_renamed.to_excel(writer, sheet_name=safe_name, index=False)
    return output.getvalue()


# ── 统计卡片 ──────────────────────────────────────────
def show_stats(df: pd.DataFrame, has_tc_info: bool = False):
    cols = st.columns(4)
    with cols[0]:
        st.markdown(
            f'<div class="stat-card"><div class="num">{len(df)}</div>'
            f'<div class="label">总条数</div></div>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        cats = df["category"].value_counts()
        label = " · ".join(f"{CAT_NAME_MAP.get(k, k)} {v}" for k, v in cats.head(3).items())
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
        if has_tc_info and "tc_code" in df.columns and df["tc_code"].str.len().sum() > 0:
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


# ── 结果展示（去重 + 中文表头 + Excel 多 Sheet）─────
def show_results(sheet_dict: Dict[str, pd.DataFrame], filename_base: str):
    """sheet_dict: {sheet_label: DataFrame}"""
    if not sheet_dict:
        return

    # 合并所有 sheet 用于总览
    all_df = pd.concat(sheet_dict.values(), ignore_index=True)

    # ── 去重 (按标准号，去掉空标准号的重复行) ──
    dup_mask = all_df["standard_code"].duplicated(keep="first")
    drop_mask = dup_mask & (all_df["standard_code"] != "")
    dups_removed = drop_mask.sum()
    all_df = all_df[~drop_mask].reset_index(drop=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card-title">📊 检索结果（共 {len(all_df)} 条）</div>',
        unsafe_allow_html=True,
    )

    if dups_removed:
        st.caption(f"已去重 {dups_removed} 条重复标准")

    # ── 筛选 ──
    with st.expander("🔍 筛选结果", expanded=False):
        filter_cols = st.columns(4)
        filters = {}
        for i, col_name in enumerate(["standard_code", "standard_name", "state", "charge_dept"]):
            if col_name in all_df.columns and all_df[col_name].nunique() > 1:
                vals = [""] + sorted(all_df[col_name].dropna().unique().tolist())
                filters[col_name] = filter_cols[i % 4].selectbox(
                    COLUMN_LABELS.get(col_name, col_name), vals, key=f"filter_{col_name}"
                )

    filtered = all_df.copy()
    for col_name, val in filters.items():
        if val:
            filtered = filtered[filtered[col_name] == val]

    has_tc = "tc_code" in all_df.columns and all_df["tc_code"].str.len().sum() > 0

    col_left, col_mid, col_right = st.columns([2, 1, 1])
    with col_left:
        st.caption(f"当前筛选后: {len(filtered)} 条")
    with col_mid:
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        now = time.strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 下载 CSV",
            csv,
            f"{filename_base}_{now}.csv",
            "text/csv",
        )
    with col_right:
        # 多 Sheet Excel 下载
        if len(sheet_dict) > 1:
            excel_bytes = make_multisheet_excel(sheet_dict)
            st.download_button(
                "📥 下载 Excel",
                excel_bytes,
                f"{filename_base}_{now}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # 显示表格（中文表头）
    display_df = rename_cols(filtered)
    st.dataframe(display_df, width="stretch", height=500)

    with st.expander("📈 统计概览"):
        show_stats(filtered, has_tc_info=has_tc)

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
            <p>从全国标准信息公共服务平台检索标准数据</p>
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

        results_by_cat: Dict[str, list] = {}
        bar = st.progress(0, text="准备中...")
        status = st.empty()

        for i, cat in enumerate(categories):
            name = CATEGORY_CONFIG[cat]["name"]

            # 预先获取总数
            total = get_search_total(cat, keyword.strip(), page_size=page_size)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0

            status.info(f"正在检索 {name}（共 {total} 条，{total_pages} 页）...")
            results = []
            page = 1
            for row in iter_keyword_results(cat, keyword.strip(), page_size=page_size, max_pages=max_pages):
                results.append(row)
                if len(results) % page_size == 1:
                    status.info(f"正在检索 {name}... 第 {page}/{total_pages or '?'} 页（已获取 {len(results)} 条）")
                    page += 1

            results_by_cat[name] = results
            bar.progress(
                (i + 1) / len(categories),
                text=f"已完成 {name}（{len(results)} 条）",
            )
            time.sleep(0.3)

        bar.empty()
        status.empty()

        if any(rows for rows in results_by_cat.values()):
            sheet_dict = {}
            for cat_name, rows in results_by_cat.items():
                if rows:
                    sheet_dict[cat_name] = pd.DataFrame(rows)

            st.session_state.search_results = sheet_dict
            st.session_state.search_summary = f"关键词「{keyword}」"
            show_results(sheet_dict, keyword.strip())
        else:
            st.warning("未找到匹配结果，请尝试其他关键词或类别。")

    elif st.session_state.search_results is not None:
        st.info(
            f"上次检索结果：{st.session_state.search_summary}，"
            f"共 {sum(len(v) for v in st.session_state.search_results.values())} 条"
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

        results_by_tc: Dict[str, list] = {}
        bar = st.progress(0, text="准备中...")
        status = st.empty()

        for i, name in enumerate(selected_names):
            code = tc_dict[name]

            # 预先获取总数
            total = get_tc_search_total(code, page_size=page_size)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0

            status.info(f"正在检索 {name}（{code}，共 {total} 条，{total_pages} 页）...")
            results = []
            page = 1
            for row in iter_tc_results(code, page_size=page_size):
                results.append(row)
                if len(results) % page_size == 1:
                    status.info(f"正在检索 {name}... 第 {page}/{total_pages or '?'} 页（已获取 {len(results)} 条）")
                    page += 1

            results_by_tc[name] = results
            bar.progress(
                (i + 1) / len(selected_names),
                text=f"已完成 {name}（{len(results)} 条）",
            )
            time.sleep(0.3)

        bar.empty()
        status.empty()

        if any(rows for rows in results_by_tc.values()):
            sheet_dict = {}
            for tc_name, rows in results_by_tc.items():
                if rows:
                    sheet_dict[tc_name] = pd.DataFrame(rows)

            short = "_".join(selected_names[:2]).replace(" ", "")[:50]
            show_results(sheet_dict, short)
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
