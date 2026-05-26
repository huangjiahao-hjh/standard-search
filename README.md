# 标准网站爬虫

该项目用于从全国标准信息公共服务平台检索指定关键词或 TC 标委会对应的标准，并将结果保存为 CSV 文件。支持按标准类别筛选，比如国家标准、行业标准、地方标准。

## 功能

- 支持按关键词检索标准
- 支持按类别筛选：国家标准、行业标准、地方标准
- 支持按 **TC 标委会（技术委员会）** 检索标准
- 支持列出所有可用的 TC 标委会
- 支持分页获取所有匹配结果
- 提取并保存标准号、中文标准名称、标准属性、发布日期、实施状态、主管部门、归口单位、起草单位等
- 可通过命令行传入单个关键词或关键字文件
- **图形界面**：基于 Streamlit 的可视化检索平台

## 快速启动（桌面应用）

### macOS

**方法一：双击运行**（推荐）

1. 双击 `启动.command` 文件
2. 首次运行会自动安装依赖，稍等片刻浏览器自动打开

**方法二：终端启动**

```bash
cd /Users/madanni/Desktop/标准网站爬虫
python3 launcher.py
```

### Windows

**方法一：双击运行**（推荐）

1. 双击 `启动.bat` 文件
2. 首次运行会自动安装依赖，稍等片刻浏览器自动打开

**方法二：终端启动**

```bash
cd 标准网站爬虫
python launcher.py
```

> **前置要求**：需要安装 Python 3.8+。首次启动会自动下载依赖包（约 2-3 分钟）。
>
> Windows 用户如果遇到编码问题，先执行 `chcp 65001` 再运行。

---

## 🪟 Windows 打包指南（无需安装 Python）

把应用发给 Windows 用户（对方不需要装 Python）：

### 方法一：一键打包（推荐）

在 Windows 电脑上直接双击 **`build.bat`**，脚本会自动：

1. ✅ 检测 Python → 如果没有则自动下载安装
2. ✅ 安装 PyInstaller 和依赖
3. ✅ 打包成独立 `.exe` 可执行文件
4. ✅ 自动打开输出文件夹

打包产物在 `dist/标准信息检索平台/` 目录，把这个文件夹发给任何人，双击 `标准信息检索平台.exe` 即可运行。

### 方法二：GitHub Actions 自动构建

把代码推送到 GitHub，触发自动构建：

```bash
git tag v1.0
git push origin v1.0
```

在 GitHub 仓库的 **Actions** 页面下载构建产物，支持 Windows 和 macOS 两个版本。

### 输出目录结构

```
dist/标准信息检索平台/
├── 标准信息检索平台.exe   ← 主程序，双击运行
├── _internal/              ← 运行库（勿删除）
└── ...                     ← 其他支持文件
```

> 首次启动较慢（约 10-20 秒），因为需要解压运行库。

## 安装

```bash
python3 -m pip install -r requirements.txt
```

## 使用示例

### 关键词检索（原有功能）

仅检索国家标准（默认）：

```bash
python3 scraper.py --keyword 消防 --output 消防标准.csv
```

检索国家标准和行业标准：

```bash
python3 scraper.py --keyword 消防 --category national --category industry --output results.csv
```

也可以使用逗号分隔的类别列表：

```bash
python3 scraper.py --keyword 消防 --categories national,industry --output results.csv
```

使用关键字文件：

```bash
python3 scraper.py --keywords-file keywords.txt --categories national,industry --output results.csv
```

### TC 标委会检索（新增功能）

获取所有标准归口于特定技术委员会（TC）的结果。

列出所有可用的 TC 标委会：

```bash
python3 scraper.py --list-tc
```

按 TC 标委会检索（仅国家标准，使用高级搜索 API）：

```bash
# 检索 TC90（全国太阳光伏能源系统标准化技术委员会）所有标准
python3 scraper.py --tc TC90 --output tc90_standards.csv

# 同时检索多个 TC
python3 scraper.py --tc TC90 --tc TC402 --output multi_tc.csv
```

注意：`--tc` 参数当前仅支持国家标准（national），行业标准和地方标准不支持直接 TC 检索。

## 支持的类别

- `national`：国家标准
- `industry`：行业标准
- `local`：地方标准

默认情况下如果不指定类别，则只检索 `national`（国家标准）。

## 输出字段

- keyword
- category
- standard_code
- standard_name
- standard_nature
- charge_dept
- guikou_unit
- drafting_units
- issue_date
- act_date
- state
- tc_code（TC 编号，仅 TC 检索模式有值）
- draft_staff（起草人，仅 TC 检索模式有值）
- ics（ICS 分类号，仅 TC 检索模式有值）
