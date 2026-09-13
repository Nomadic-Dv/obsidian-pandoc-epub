"""
Obsidian → EPUB 合并导出工具
将 Obsidian 多个文件夹中的笔记合并导出为中文排版友好的 EPUB

MIT License
Copyright (c) 2026 [你的名字]
"""
import subprocess
try:
    ver = subprocess.run(["pandoc", "--version"], capture_output=True, text=True, encoding="utf-8")
    print(ver.stdout.split("\n")[0])
except Exception:
    pass

    
import os
import subprocess
import glob
import re
import shutil
import urllib.parse

VERSION = "1.0.0"

# ====== 配置区 ======
TARGET_KEYWORDS = [
    "党史"
]
OUTPUT_EPUB = "党史.epub"
METADATA_FILE = "metadata.yaml"
TEMP_DIR = "_temp_epub_build"
VAULT_ROOT = os.path.abspath(".")
MISSING_REPORT = "缺失引用报告.txt"    # 缺失清单文件名

# 可能的附件目录（用于补全扩展名时查找）
ASSET_DIRS = ["assets", "attachments", "images", "files", "media", "Attachments"]

# 常见图片扩展名
IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
# ====================


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def downgrade_headings(content, levels=2):
    """
    把 Markdown 里所有标题降 N 级：
    levels=2 时：# -> ###，## -> ####，...
    跳过代码块里的 #
    """
    lines = content.split('\n')
    in_code_block = False
    new_lines = []

    for line in lines:
        stripped = line.lstrip()

        if stripped.startswith('```') or stripped.startswith('~~~'):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue

        if in_code_block:
            new_lines.append(line)
            continue

        m = re.match(r'^(#{1,6})(\s+.*)$', line)
        if m:
            hashes = m.group(1)
            rest = m.group(2)
            new_count = min(len(hashes) + levels, 6)
            new_lines.append('#' * new_count + rest)
        else:
            new_lines.append(line)

    return '\n'.join(new_lines)


def convert_folders_to_epub(target_keywords, output_epub):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    all_dirs = [d for d in os.listdir(VAULT_ROOT)
                if os.path.isdir(os.path.join(VAULT_ROOT, d))
                and not d.startswith('.')
                and not d.startswith('_')]

    print(f"当前目录下的文件夹：{all_dirs}\n")

    matched_dirs = []
    for kw in target_keywords:
        matched = [d for d in all_dirs if kw in d]
        if matched:
            matched_dirs.append(matched[0])
            print(f"✅ 关键词 '{kw}' 匹配到：{matched[0]}")
        else:
            print(f"⚠️ 关键词 '{kw}' 没匹配到任何文件夹")

    if not matched_dirs:
        print("❌ 没有匹配到任何文件夹！")
        return

    new_files = []
    file_index = 0
    img_counter = 0
    missing_imgs = 0
    missing_list = []      # 收集缺失引用
    current_file = ""      # 追踪当前 md 文件

    for folder in matched_dirs:
        # 1. 先插入"文件夹章节分隔页"
        chapter_file_name = f"{file_index:03d}_章节_{folder}.md"
        chapter_file_path = os.path.join(TEMP_DIR, chapter_file_name)
        with open(chapter_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {folder}\n")
        new_files.append(chapter_file_path)
        file_index += 1

        # 2. 收集该文件夹下的 md
        search_path = os.path.join(folder, "**", "*.md")
        files = glob.glob(search_path, recursive=True)
        files.sort(key=natural_sort_key)
        print(f"📁 {folder}：找到 {len(files)} 个 md 文件")

        # 3. 逐个处理
        for file_path in files:
            current_file = file_path     # 记录当前处理的文件

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # --- 处理图片 ---
            def fix_image_path(match):
                nonlocal img_counter, missing_imgs, current_file
                alt_text = match.group(1)
                img_path = match.group(2)

                if img_path.startswith('http'):
                    return match.group(0)

                img_path_decoded = urllib.parse.unquote(img_path)

                # 判断是否"无扩展名的孤立引用"
                last_segment = img_path_decoded.replace('\\', '/').split('/')[-1]
                is_orphan = ('.' not in last_segment)

                candidates = []

                # 方式1：相对当前 md
                candidates.append(os.path.abspath(
                    os.path.join(os.path.dirname(file_path), img_path_decoded)
                ))

                # 方式2：相对仓库根目录（去掉前导 ../ 和 ./）
                clean_path = img_path_decoded
                while clean_path.startswith('../') or clean_path.startswith('./'):
                    if clean_path.startswith('../'):
                        clean_path = clean_path[3:]
                    else:
                        clean_path = clean_path[2:]
                candidates.append(os.path.abspath(os.path.join(VAULT_ROOT, clean_path)))

                # 方式3：绝对路径
                candidates.append(os.path.abspath(img_path_decoded))

                # 方式4：如果是孤立引用，尝试补常见图片后缀
                # ★ 修复：不硬编码 assets，遍历所有可能的附件目录
                if is_orphan:
                    for ext in IMAGE_EXTS:
                        # 4a. 仓库根目录直接补扩展名
                        candidates.append(os.path.join(VAULT_ROOT, clean_path + ext))
                        # 4b. 遍历所有可能的附件目录
                        for ad in ASSET_DIRS:
                            candidates.append(os.path.join(VAULT_ROOT, ad, clean_path + ext))
                            candidates.append(os.path.join(VAULT_ROOT, ad, last_segment + ext))
                            # 4c. 附件目录下再按原始相对路径查找
                            candidates.append(os.path.join(VAULT_ROOT, ad, clean_path))

                abs_img_path = None
                for c in candidates:
                    if os.path.exists(c):
                        abs_img_path = c
                        break

                if abs_img_path is None:
                    missing_imgs += 1
                    # 记入缺失清单
                    missing_list.append({
                        'file': current_file,
                        'ref': img_path,
                        'alt': alt_text,
                        'is_orphan': is_orphan
                    })
                    # 在 EPUB 里显示可见提示
                    if is_orphan:
                        return f"\n\n> 🔗 **无效引用**（可能是笔记链接或已删除附件）：`{img_path}`\n\n"
                    else:
                        return f"\n\n> ⚠️ **图片缺失**：`{img_path}`\n\n"

                ext = os.path.splitext(abs_img_path)[1]
                new_img_name = f"img_{img_counter:05d}{ext}"
                img_counter += 1
                new_img_path = os.path.join(TEMP_DIR, new_img_name)
                shutil.copy2(abs_img_path, new_img_path)

                return f"![{alt_text}]({new_img_name})"

            content = re.sub(r'!\[(.*?)\]\((.*?)\)', fix_image_path, content)

            # --- 标题降级 ---
            content = downgrade_headings(content, levels=2)

            # --- 用文件名作为二级标题 ---
            file_basename = os.path.splitext(os.path.basename(file_path))[0]
            title = re.sub(r'^\d+[_\-\s]+', '', file_basename)

            final_content = f"## {title}\n\n{content}"

            new_file_name = f"{file_index:03d}_{os.path.basename(file_path)}"
            new_file_path = os.path.join(TEMP_DIR, new_file_name)
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)

            new_files.append(new_file_path)
            file_index += 1

    print(f"\n✅ 图片处理：成功复制 {img_counter} 张，缺失 {missing_imgs} 张")
    print(f"✅ 共生成 {file_index} 个临时 md 文件（含 {len(matched_dirs)} 个文件夹章节）")

    # 生成缺失引用报告
    if missing_list:
        with open(MISSING_REPORT, 'w', encoding='utf-8') as f:
            f.write(f"共 {len(missing_list)} 个缺失/无效引用\n")
            f.write("=" * 70 + "\n\n")
            for i, item in enumerate(missing_list, 1):
                f.write(f"[{i}] 文件：{item['file']}\n")
                f.write(f"    引用：{item['ref']}\n")
                if item['alt']:
                    f.write(f"    说明：{item['alt']}\n")
                f.write(f"    类型：{'无效引用（无扩展名）' if item['is_orphan'] else '图片缺失'}\n")
                f.write("\n")
        print(f"\n📋 缺失引用清单已保存：{MISSING_REPORT}")
        print("   请在 Obsidian 中打开对应文件，逐一检查修复。")

    if img_counter == 0:
        print("\n⚠️ 一张图片都没复制成功。")
        return

    print("正在执行 Pandoc 转换...")

    cmd = ["pandoc"] + new_files + [
        "-o", output_epub,
        "--toc",
        "--toc-depth=2",
        "--from=markdown+pipe_tables",
        "--resource-path=" + TEMP_DIR,
        "--embed-resources",
        "--standalone",
        "--css=epub-style.css",
        "--split-level=2",
        "--include-before-body=body-open.html",    # ← 插入 <div ...>
        "--include-after-body=body-close.html",    # ← 插入 </div>
        "--epub-embed-font=fonts/苹方字体.ttf",   # 新增：嵌入字体

    ]

    if os.path.exists(METADATA_FILE):
        cmd.insert(1, METADATA_FILE)

    try:
        result = subprocess.run(
            cmd, check=True,
            capture_output=True, text=True,
            encoding='utf-8', errors='replace'
        )
        print(f"\n✅ 转换成功！文件已保存为：{output_epub}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 转换失败！")
        print(f"错误代码：{e.returncode}")
        if e.stderr:
            stderr_lines = e.stderr.strip().split('\n')
            print("Pandoc 错误输出（最后20行）：")
            for line in stderr_lines[-20:]:
                print("  " + line)
    except FileNotFoundError:
        print("\n❌ 错误：未找到 Pandoc")


if __name__ == "__main__":
    print(f"Obsidian → EPUB 合并导出工具 v{VERSION}\n")
    convert_folders_to_epub(TARGET_KEYWORDS, OUTPUT_EPUB)