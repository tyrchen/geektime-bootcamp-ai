---
description: 扫描并优化仓库中的所有图片
argument-hint: [format] [quality] [backup]
allowed-tools: Bash(find:*), Bash(which:*), Bash(file:*), Bash(mkdir:*), Bash(cp:*), Bash(mv:*)
---

# 优化图片

我将帮助你扫描仓库中的所有图片文件并优化它们。支持多种优化工具和方法。

## 步骤 1: 检查可用的优化工具

首先检查系统中可用的图片优化工具：

### 检查 ImageMagick

!`which convert magick 2>/dev/null | head -1 || echo "未找到 ImageMagick"`

### 检查 sharp-cli (Node.js)

!`which sharp-cli 2>/dev/null || echo "未找到 sharp-cli"`

### 检查 optipng

!`which optipng 2>/dev/null || echo "未找到 optipng"`

### 检查 jpegoptim

!`which jpegoptim 2>/dev/null || echo "未找到 jpegoptim"`

### 检查 cwebp (WebP)

!`which cwebp 2>/dev/null || echo "未找到 cwebp"`

## 步骤 2: 扫描图片文件

扫描仓库中的所有图片文件（排除 node_modules、.git 等目录）：

```bash
# 查找所有图片文件
find . -type f \( \
  -iname "*.png" -o \
  -iname "*.jpg" -o \
  -iname "*.jpeg" -o \
  -iname "*.gif" -o \
  -iname "*.webp" -o \
  -iname "*.bmp" -o \
  -iname "*.tiff" -o \
  -iname "*.tif" \
\) ! -path "*/node_modules/*" \
  ! -path "*/.git/*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/.cache/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/venv/*" \
  ! -path "*/env/*" \
  | sort
```

### 统计图片文件

!`find . -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.gif" -o -iname "*.webp" -o -iname "*.bmp" -o -iname "*.tiff" -o -iname "*.tif" \) ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/.next/*" ! -path "*/dist/*" ! -path "*/build/*" ! -path "*/.cache/*" ! -path "*/__pycache__/*" ! -path "*/venv/*" ! -path "*/env/*" | wc -l | tr -d ' '`

### 按类型分类统计

!`find . -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.gif" -o -iname "*.webp" \) ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/.next/*" ! -path "*/dist/*" ! -path "*/build/*" ! -path "*/.cache/*" ! -path "*/__pycache__/*" ! -path "*/venv/*" ! -path "*/env/*" -exec sh -c 'case "$1" in *.png) echo "PNG";; *.jpg|*.jpeg) echo "JPEG";; *.gif) echo "GIF";; *.webp) echo "WebP";; esac' _ {} \; | sort | uniq -c | sort -rn`

## 步骤 3: 创建备份（可选）

如果指定了 `backup` 参数，创建备份目录：

```bash
BACKUP_DIR=".image-backup-$(date +%Y%m%d-%H%M%S)"
if [ "$3" = "backup" ] || [ -n "$3" ]; then
  echo "创建备份目录: $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"

  # 备份所有图片文件
  find . -type f \( \
    -iname "*.png" -o \
    -iname "*.jpg" -o \
    -iname "*.jpeg" -o \
    -iname "*.gif" -o \
    -iname "*.webp" \
  \) ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    ! -path "*/.next/*" \
    ! -path "*/dist/*" \
    ! -path "*/build/*" \
    ! -path "*/.cache/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/venv/*" \
    ! -path "*/env/*" \
    -exec sh -c 'mkdir -p "$1/$(dirname "$2")" && cp "$2" "$1/$2"' _ "$BACKUP_DIR" {} \;

  echo "备份完成: $BACKUP_DIR"
fi
```

## 步骤 4: 优化图片

根据可用的工具选择优化方法：

### 方法 1: 使用 ImageMagick（如果可用）

```bash
if command -v magick &> /dev/null || command -v convert &> /dev/null; then
  CONVERT_CMD=$(which magick 2>/dev/null || which convert 2>/dev/null)
  QUALITY=${2:-85}
  FORMAT=${1:-"keep"}

  echo "使用 ImageMagick 优化图片..."
  echo "质量: $QUALITY%"
  echo "格式: $FORMAT"

  find . -type f \( \
    -iname "*.png" -o \
    -iname "*.jpg" -o \
    -iname "*.jpeg" -o \
    -iname "*.gif" \
  \) ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    ! -path "*/.next/*" \
    ! -path "*/dist/*" \
    ! -path "*/build/*" \
    ! -path "*/.cache/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/venv/*" \
    ! -path "*/env/*" \
    -exec sh -c '
      file="$1"
      ext="${file##*.}"
      name="${file%.*}"

      if [ "$3" = "webp" ]; then
        "$2" "$file" -quality "$4" "$name.webp" && echo "优化: $file -> $name.webp"
      elif [ "$3" = "keep" ]; then
        if [ "$ext" = "png" ]; then
          "$2" "$file" -strip -quality "$4" "$file" && echo "优化: $file"
        else
          "$2" "$file" -strip -quality "$4" "$file" && echo "优化: $file"
        fi
      else
        "$2" "$file" -strip -quality "$4" "$file.$3" && echo "转换: $file -> $file.$3"
      fi
    ' _ {} "$CONVERT_CMD" "$FORMAT" "$QUALITY" \;
fi
```

### 方法 2: 使用 optipng 和 jpegoptim（如果可用）

```bash
if command -v optipng &> /dev/null || command -v jpegoptim &> /dev/null; then
  echo "使用 optipng/jpegoptim 优化图片..."

  # 优化 PNG
  if command -v optipng &> /dev/null; then
    find . -type f -iname "*.png" \
      ! -path "*/node_modules/*" \
      ! -path "*/.git/*" \
      ! -path "*/.next/*" \
      ! -path "*/dist/*" \
      ! -path "*/build/*" \
      ! -path "*/.cache/*" \
      ! -path "*/__pycache__/*" \
      ! -path "*/venv/*" \
      ! -path "*/env/*" \
      -exec optipng -o2 -quiet {} \; \
      -exec echo "优化 PNG: {}" \;
  fi

  # 优化 JPEG
  if command -v jpegoptim &> /dev/null; then
    QUALITY=${2:-85}
    find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" \) \
      ! -path "*/node_modules/*" \
      ! -path "*/.git/*" \
      ! -path "*/.next/*" \
      ! -path "*/dist/*" \
      ! -path "*/build/*" \
      ! -path "*/.cache/*" \
      ! -path "*/__pycache__/*" \
      ! -path "*/venv/*" \
      ! -path "*/env/*" \
      -exec jpegoptim --max="$QUALITY" --strip-all --preserve --quiet {} \; \
      -exec echo "优化 JPEG: {}" \;
  fi
fi
```

### 方法 3: 使用 cwebp 转换为 WebP（如果可用）

```bash
if command -v cwebp &> /dev/null && [ "$1" = "webp" ]; then
  QUALITY=${2:-85}
  echo "使用 cwebp 转换为 WebP..."
  echo "质量: $QUALITY%"

  find . -type f \( \
    -iname "*.png" -o \
    -iname "*.jpg" -o \
    -iname "*.jpeg" \
  \) ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    ! -path "*/.next/*" \
    ! -path "*/dist/*" \
    ! -path "*/build/*" \
    ! -path "*/.cache/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/venv/*" \
    ! -path "*/env/*" \
    -exec sh -c '
      file="$1"
      name="${file%.*}"
      cwebp -q "$2" "$file" -o "$name.webp" && echo "转换: $file -> $name.webp"
    ' _ {} "$QUALITY" \;
fi
```

### 方法 4: 使用 Python Pillow（如果可用）

```bash
if command -v python3 &> /dev/null; then
  echo "尝试使用 Python Pillow 优化图片..."

  python3 << 'PYTHON_SCRIPT'
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("未安装 Pillow，跳过 Python 优化")
    sys.exit(0)

def optimize_image(file_path, quality=85, format_override=None):
    try:
        with Image.open(file_path) as img:
            # 转换为 RGB（如果需要）
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                img = background

            # 确定输出格式
            ext = Path(file_path).suffix.lower()
            if format_override:
                output_format = format_override.upper()
                output_path = str(Path(file_path).with_suffix(f'.{format_override}'))
            else:
                output_format = 'JPEG' if ext in ['.jpg', '.jpeg'] else 'PNG'
                output_path = file_path

            # 保存优化后的图片
            if output_format == 'JPEG':
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            else:
                img.save(output_path, 'PNG', optimize=True)

            return True
    except Exception as e:
        print(f"错误处理 {file_path}: {e}")
        return False

# 扫描图片文件
exclude_dirs = {'node_modules', '.git', '.next', 'dist', 'build', '.cache', '__pycache__', 'venv', 'env'}
image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif'}

quality = int(sys.argv[1]) if len(sys.argv) > 1 else 85
format_override = sys.argv[2] if len(sys.argv) > 2 else None

count = 0
for root, dirs, files in os.walk('.'):
    # 排除目录
    dirs[:] = [d for d in dirs if d not in exclude_dirs]

    for file in files:
        file_path = Path(root) / file
        if file_path.suffix.lower() in image_extensions:
            if optimize_image(str(file_path), quality, format_override):
                count += 1
                print(f"优化: {file_path}")

print(f"\n共优化 {count} 个图片文件")
PYTHON_SCRIPT
fi
```

## 步骤 5: 显示优化结果

优化完成后，显示文件大小对比：

```bash
echo "=== 优化结果 ==="
echo ""
echo "图片文件统计:"
find . -type f \( \
  -iname "*.png" -o \
  -iname "*.jpg" -o \
  -iname "*.jpeg" -o \
  -iname "*.gif" -o \
  -iname "*.webp" \
\) ! -path "*/node_modules/*" \
  ! -path "*/.git/*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/.cache/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/venv/*" \
  ! -path "*/env/*" \
  -exec sh -c 'echo "$(du -h "$1" | cut -f1) - $1"' _ {} \; | sort -h
```

**使用方法：**

- `/optimize-images` - 扫描并优化所有图片（保持原格式）
- `/optimize-images webp` - 将所有图片转换为 WebP 格式
- `/optimize-images keep 90` - 优化图片，质量设置为 90%
- `/optimize-images webp 85 backup` - 转换为 WebP，质量 85%，并创建备份

**参数说明：**

- `format` (第一个参数):
  - `keep` 或留空 - 保持原格式
  - `webp` - 转换为 WebP 格式
  - 其他格式名称 - 转换为指定格式

- `quality` (第二个参数):
  - 数字 1-100，默认 85
  - 仅对 JPEG 和 WebP 有效

- `backup` (第三个参数):
  - 如果提供，会在优化前创建备份

**推荐工具安装：**

- **macOS**: `brew install imagemagick optipng jpegoptim webp`
- **Ubuntu/Debian**: `sudo apt-get install imagemagick optipng jpegoptim webp`
- **Python Pillow**: `pip install Pillow`

**注意事项：**

- 优化会直接修改原文件（除非转换为新格式）
- 建议先使用 `backup` 参数创建备份
- 某些工具可能需要单独安装
- SVG 文件不会被优化（矢量图不需要优化）
- 大文件优化可能需要较长时间
