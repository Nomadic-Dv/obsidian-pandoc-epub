[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Pandoc](https://img.shields.io/badge/Pandoc-3.0%2B-blue.svg)](https://pandoc.org/)
[![GitHub stars](https://img.shields.io/github/stars/Nomadic-Dv/obsidian-pandoc-epub.svg)](https://github.com/Nomadic-Dv/obsidian-pandoc-epub/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/Nomadic-Dv/obsidian-pandoc-epub.svg)](https://github.com/Nomadic-Dv/obsidian-pandoc-epub/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/Nomadic-Dv/obsidian-pandoc-epub.svg)](https://github.com/Nomadic-Dv/obsidian-pandoc-epub/commits/main)


# Obsidian → EPUB 合并导出工具

> **把分散在多文件夹里的 Obsidian 笔记，合并成一本排版精美的 EPUB。**
> 文件夹 → 一级标题 · 笔记文件 → 二级标题 · 图片自动嵌入 · 中文排版友好。
> 全程纯 Python + Pandoc，无需任何 pip 依赖。

## 功能特性

- **多文件夹合并**：把 Obsidian 里多个顶层文件夹（例如"财富 | 赚钱"、"反焦虑 | 治愈 | 励志"、"思考"）合并为一本 EPUB
- **层级清晰**：文件夹名 → 一级标题（H1），笔记文件名 → 二级标题（H2），笔记内原有标题自动降级
- **图片自动嵌入**：自动处理 Obsidian 的图片引用，URL 解码、补全扩展名、嵌入 EPUB
- **中文排版友好**：正文首行缩进 2 字符，宋体正文 + 黑体标题，行距 1.75
- **每个笔记独立分章**：EPUB 内部一个笔记一个 HTML 文件，翻页干净
- **缺失引用报告**：自动生成 `缺失引用报告.txt`，列出所有找不到的图片引用，方便回到 Obsidian 修复

## 效果预览

```
📖 我的笔记合集
├── 财富 | 赚钱                ← H1（文件夹）
│   ├── 普通人赚钱最快的方法     ← H2（笔记文件名）
│   │   ├── 一些笔记内的一级标题  ← 原 # 降级为 H3
│   │   └── ...
│   ├── 富爸爸说的被动收入...    ← H2
│   └── ...（该文件夹下 37 篇笔记）
├── 反焦虑 | 治愈 | 励志         ← H1
│   └── ...（44 篇笔记）
└── 思考                       ← H1
    └── ...（153 篇笔记）
```

## 环境要求

| 依赖     | 版本要求              | 说明                                    |
| ------ | ----------------- | ------------------------------------- |
| Python | 3.7+              | 运行转换脚本                                |
| Pandoc | **3.0+**（推荐 3.1+） | 核心转换工具，`--epub-chapter-level` 需要 3.0+ |

### 安装 Pandoc

- **Windows**：[pandoc.org/installing](https://pandoc.org/installing.html) 下载安装包，安装后重启终端
- **macOS**：`brew install pandoc`
- **Linux**：`sudo apt install pandoc`

安装完成后，在终端验证：

```bash
pandoc --version
```

应该输出 `pandoc 3.x.x` 或更高。

## 目录结构

把 `convert.py`、`epub-style.css`、`metadata.yaml` 放在 Obsidian 仓库的**根目录**（即和你的笔记文件夹同级）：

```
你的 Obsidian 仓库/  
├── convert.py               ← 主脚本  
├── epub-style.css           ← EPUB 样式表（首行缩进 2 字符 + iBooks 日夜间颜色）  
├── metadata.yaml            ← 电子书元数据（书名、作者）  
├── metadata.yaml.example    ← 元数据示例文件（复制后改名为 metadata.yaml）  
├── body-open.html           ← Pandoc 模板：<body> 开标签（可选）  
├── body-close.html          ← Pandoc 模板：</body> 闭标签（可选）  
├── assets/                  ← 你的图片附件目录  
├── fonts/                   ← 嵌入字体目录（可选，iBooks 自定义字体用）  
│ ├── SourceHanSans-Regular.otf  
│ └── SourceHanSans-Bold.otf  
├── 财富 | 赚钱/                            ← 要合并的文件夹 1  
├── 反焦虑 | 治愈 | 励志/                    ← 要合并的文件夹 2  
├── 思考/                                  ← 要合并的文件夹 3  
├── CHANGELOG.md                          ← 版本历史  
├── LICENSE                               ← MIT 许可证  
├── README.md                             ← 本文件  
└── ...                                   （其他笔记文件夹不参与合并）
```

## 快速开始

### 第一步：准备三个文件

**1. `metadata.yaml`**（电子书元数据，从仓库中的 `metadata.yaml.example` 复制并改名）：

```yaml
---
title: 我的笔记合集
author: 你的名字
lang: zh-CN
---
```

**2. `epub-style.css`**（中文排版样式，见 [样式表](#样式表) 一节）

**3. `convert.py`**（主脚本，见 [完整脚本](#完整脚本) 一节）

### 第二步：修改脚本配置

打开 `convert.py`，找到配置区：

```python
# ====== 配置区 ======
TARGET_KEYWORDS = [
    "财富",       # 匹配包含"财富"的文件夹
    "反焦虑",     # 匹配包含"反焦虑"的文件夹
    "思考"        # 匹配包含"思考"的文件夹
]
OUTPUT_EPUB = "我的合集.epub"       # 输出文件名
METADATA_FILE = "metadata.yaml"     # 元数据文件
TEMP_DIR = "_temp_epub_build"       # 临时工作目录
VAULT_ROOT = os.path.abspath(".")   # 仓库根目录（当前目录）
MISSING_REPORT = "缺失引用报告.txt"   # 缺失引用报告文件名
# ====================
```

- `TARGET_KEYWORDS`：**按文件夹名的关键词匹配**（用关键词而非全名，避免全角/半角字符导致的路径不匹配问题）
- `OUTPUT_EPUB`：生成的 EPUB 文件名

### 第三步：运行

在仓库根目录打开终端：

```bash
python convert.py
```

预期输出：

```
当前目录下的文件夹：['assets', '反焦虑 | 治愈 | 励志', '思考', '财富 | 赚钱']

✅ 关键词 '财富' 匹配到：财富 | 赚钱
✅ 关键词 '反焦虑' 匹配到：反焦虑 | 治愈 | 励志
✅ 关键词 '思考' 匹配到：思考
📁 财富 | 赚钱：找到 37 个 md 文件
📁 反焦虑 | 治愈 | 励志：找到 44 个 md 文件
📁 思考：找到 153 个 md 文件

✅ 图片处理：成功复制 566 张，缺失 6 张
✅ 共生成 237 个临时 md 文件（含 3 个文件夹章节）

📋 缺失引用清单已保存：缺失引用报告.txt
正在执行 Pandoc 转换...

✅ 转换成功！文件已保存为：我的合集.epub
```

生成的 `我的合集.epub` 就可以用任意 EPUB 阅读器打开了。


## 许可

MIT License。你可以自由修改、分发、商用。

## 贡献

欢迎提交 Issue 和 PR。如果你有更好的中文 EPUB 排版建议，欢迎交流。


## 相关项目

- [epub-weasyprint-pdf](https://github.com/Nomadic-Dv/epub-weasyprint-pdf) —— 把 EPUB 转成出版级排版的 PDF（WeasyPrint 实现）  
  👉 **工作流**：Obsidian → EPUB → PDF