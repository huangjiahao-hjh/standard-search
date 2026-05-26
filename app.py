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
    .stApp header {display: none;}
    .main-title {font-size: 2.2rem; font-weight: 700; margin-bottom: 0;}
    .sub-title {color: #666; margin-bottom: 1.5rem;}
    .stat-box {background: #f0f2f6; border-radius: 10px; padding: 1rem; text-align: center;}
    .stat-box .num {font-size: 2rem; font-weight: 700; color: #0068c9;}
    .stat-box .label {font-size: 0.85rem; color: #666;}
</style>
""",
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


# ── 缓存 TC 列表（避免重复请求） ───────────────────────
@st.cache_data(ttl=3600, show_spinner="正在加载 TC 列表...")
def load_tc_committees():
    committees = fetch_tc_committees()
    return committees, {c["name"]: c["code"] for c in committees}


# ── 统计卡片 ──────────────────────────────────────────
def show_stats(df):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="stat-box"><div class="num">{len(df)}</div>'
            f'<div class="label">总条数</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        cats = df["category"].value_counts()
        cat_names = {k: v["name"] for k, v in CATEGORY_CONFIG.items()}
        label = ", ".join(
            f"{cat_names.get(k, k)} {v}" for k, v in cats.head(3).items()
        )
        st.markdown(
            f'<div class="stat-box"><div class="num">{len(cats)}</div>'
            f"<div class=\"label\">标准类别<br><small>{label}</small></div></div>",
            unsafe_allow_html=True,
        )
    with col3:
        states = df["state"].value_counts()
        label = ", ".join(f"{k} {v}" for k, v in states.head(3).items())
        st.markdown(
            f'<div class="stat-box"><div class="num">{len(states)}</div>'
            f"<div class=\"label\">实施状态<br><small>{label}</small></div></div>",
            unsafe_allow_html=True,
        )
    with col4:
        if "tc_code" in df.columns and df["tc_code"].str.len().sum() > 0:
            tcs = df["tc_code"].value_counts()
            valid = tcs[tcs.index != ""]
            label = ", ".join(f"{k}" for k in valid.head(3).index)
            st.markdown(
                f'<div class="stat-box"><div class="num">{len(valid)}</div>'
                f"<div class=\"label\">关联 TC<br><small>{label}</small></div></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="stat-box"><div class="num">—</div>'
                '<div class="label">关联 TC</div></div>',
                unsafe_allow_html=True,
            )


# ── 结果数据框 + 下载 ───────────────────────────────
def show_results(df, filename_base):
    st.divider()
    st.subheader(f"📊 检索结果（共 {len(df)} 条）")

    # 内联筛选
    with st.expander("🔍 筛选结果", expanded=False):
        cols = st.columns(4)
        filters = {}
        for i, col_name in enumerate(
            ["standard_code", "standard_name", "state", "charge_dept"]
        ):
            if col_name in df.columns and df[col_name].nunique() > 1:
                unique_vals = [""] + sorted(
                    df[col_name].dropna().unique().tolist()
                )
                filters[col_name] = cols[i % 4].selectbox(
                    col_name, unique_vals, key=f"filter_{col_name}"
                )

    filtered = df.copy()
    for col_name, val in filters.items():
        if val:
            filtered = filtered[filtered[col_name] == val]

    col_count, col_export = st.columns([1, 1])
    with col_count:
        st.caption(f"当前筛选后: {len(filtered)} 条")
    with col_export:
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        now = time.strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 下载 CSV",
            csv,
            f"{filename_base}_{now}.csv",
            "text/csv",
            width="stretch",
        )

    st.dataframe(filtered, width="stretch", height=500)

    with st.expander("📈 统计概览"):
        show_stats(filtered)


# ══════════════════════════════════════════════════════
#  侧边栏导航
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📋 标准检索平台")
    st.markdown("---")

    mode = st.radio(
        "选择功能",
        ["🔑 关键词检索", "🏷️ TC 标委会检索", "📋 TC 标委会列表"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption(
        "数据来源：全国标准信息公共服务平台\n"
    )

# ══════════════════════════════════════════════════════
#  主界面
# ══════════════════════════════════════════════════════

st.markdown(
    '<div class="main-title">📋 全国标准信息检索平台</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">从全国标准信息公共服务平台检索标准数据，'
    "支持关键词检索和 TC 标委会检索</div>",
    unsafe_allow_html=True,
)


# ── 模式 1：关键词检索 ─────────────────────────────
if "关键词" in mode:
    st.header("🔑 关键词检索")

    with st.container(border=True):
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

        col_ps, col_mp = st.columns(2)
        with col_ps:
            page_size = st.number_input(
                "每页条数", min_value=5, max_value=100, value=15, step=5
            )
        with col_mp:
            max_pages = st.number_input(
                "最大页数（0=不限）",
                min_value=0,
                max_value=200,
                value=0,
                step=1,
                help="限制抓取页数以节省时间",
            )

        search_clicked = st.button("🚀 开始检索", type="primary", width="stretch")

    if search_clicked:
        if not keyword.strip():
            st.warning("请输入关键词")
            st.stop()
        if not categories:
            st.warning("请选择至少一个标准类别")
            st.stop()

        results = []
        progress_bar = st.progress(0, text="准备中...")
        status_text = st.empty()

        total_cats = len(categories)
        for i, cat in enumerate(categories):
            cat_name = CATEGORY_CONFIG[cat]["name"]
            status_text.info(f"正在检索 {cat_name}...")

            count = 0
            for row in iter_keyword_results(
                cat, keyword.strip(),
                page_size=page_size, max_pages=max_pages,
            ):
                results.append(row)
                count += 1
            progress_bar.progress(
                (i + 1) / total_cats,
                text=f"已完成 {cat_name} ({count} 条)",
            )
            time.sleep(0.3)

        progress_bar.empty()
        status_text.empty()

        if results:
            df = pd.DataFrame(results)
            st.session_state.search_results = df
            st.session_state.search_summary = f"关键词「{keyword}」"
            show_results(df, keyword.strip())
        else:
            st.warning("未找到匹配结果，请尝试其他关键词或类别。")

    # 显示上次结果（如果此次未检索）
    elif st.session_state.search_results is not None:
        st.info(f"上次检索结果：{st.session_state.search_summary}，"
                f"共 {len(st.session_state.search_results)} 条")
        if st.button("显示上次结果"):
            show_results(
                st.session_state.search_results,
                st.session_state.search_summary.replace(" ", "_"),
            )


# ── 模式 2：TC 标委会检索 ──────────────────────────
elif "TC 标委会检索" in mode:
    st.header("🏷️ TC 标委会检索")

    committees, tc_dict = load_tc_committees()

    if not committees:
        st.error("无法获取 TC 列表，请检查网络连接后刷新页面。")
        st.stop()

    with st.container(border=True):
        tc_names = list(tc_dict.keys())
        selected_names = st.multiselect(
            "选择 TC 标委会",
            options=tc_names,
            placeholder="输入名称搜索...",
            help="可搜索并多选",
        )

        page_size = st.number_input(
            "每页条数",
            min_value=5, max_value=100, value=50, step=5,
            key="tc_page_size",
        )

        tc_search_clicked = st.button(
            "🚀 开始检索", type="primary", width="stretch"
        )

    if tc_search_clicked:
        if not selected_names:
            st.warning("请选择至少一个 TC 标委会")
            st.stop()

        results = []
        progress_bar = st.progress(0, text="准备中...")
        status_text = st.empty()

        total = len(selected_names)
        for i, name in enumerate(selected_names):
            code = tc_dict[name]
            status_text.info(f"正在检索 {name} ({code})...")
            count = 0
            for row in iter_tc_results(code, page_size=page_size):
                results.append(row)
                count += 1
            progress_bar.progress(
                (i + 1) / total,
                text=f"已完成 {name} ({count} 条)",
            )
            time.sleep(0.3)

        progress_bar.empty()
        status_text.empty()

        if results:
            df = pd.DataFrame(results)
            short_name = "_".join(selected_names[:2]).replace(
                " ", ""
            )[:50]
            show_results(df, short_name)
        else:
            st.warning("未找到匹配结果。")


# ── 模式 3：TC 标委会列表 ──────────────────────────
elif "TC 标委会列表" in mode:
    st.header("📋 TC 标委会列表")

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

        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"共 {len(committees)} 个标委会，当前筛选 {len(df_tc)} 个")
        with col2:
            csv_tc = df_tc.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 下载列表",
                csv_tc,
                "tc_list.csv",
                "text/csv",
            )

        st.dataframe(
            df_tc,
            width="stretch",
            height=600,
            column_config={
                "code": st.column_config.TextColumn("编号", width="small"),
                "name": st.column_config.TextColumn("名称", width="large"),
            },
        )
