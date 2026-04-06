# 扫描版 PDF 内容提取工具 - 安装与使用指南

## 📋 概述

本工具用于从扫描版 PDF（如《图解六壬大全》）中提取指定页面内容，支持 OCR 文字识别。

**目标：** 提取第 290 页的"三光课"内容

---

## 🛠️ 安装步骤

### 步骤 1：安装 Python 依赖包

打开命令行（CMD 或 PowerShell），执行：

```bash
cd "d:\新建文件夹\仪度六壬择日\yiduluren\zongmen"
pip install pdf2image pytesseract pillow pdfplumber
```

**如果遇到错误：**

#### 错误 1：`pip` 未安装
```bash
# 下载 get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

#### 错误 2：下载速度慢
```bash
# 使用国内镜像
pip install pdf2image pytesseract pillow pdfplumber -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 2：安装 Tesseract-OCR 引擎

Tesseract-OCR 是 OCR 识别的核心引擎，必须安装。

#### Windows 安装：

1. **下载安装包**
   - 访问：https://github.com/UB-Mannheim/tesseract/wiki
   - 下载：`tesseract-ocr-w64-setup-5.x.x.exe`（64 位）

2. **安装**
   - 双击运行安装程序
   - 选择安装路径（建议：`C:\Program Files\Tesseract-OCR`）
   - **重要：** 勾选"Additional language data"中的"Chinese (Simplified)"

3. **配置环境变量**
   - 右键"此电脑" → "属性" → "高级系统设置"
   - "环境变量" → 在"系统变量"中找到"Path"
   - "编辑" → "新建" → 添加：`C:\Program Files\Tesseract-OCR`
   - 确定保存

4. **验证安装**
   ```bash
   tesseract --version
   ```
   应该显示版本信息

#### 如果无法访问 GitHub：

**备用下载：**
- 百度网盘：https://pan.baidu.com/s/1xxx（请自行搜索）
- 提取码：xxxx

### 步骤 3：安装中文语言包（如果步骤 2 未安装）

1. 下载中文语言包：
   - 访问：https://github.com/tesseract-ocr/tessdata
   - 下载：`chi_sim.traineddata`（简体）或 `chi_tra.traineddata`（繁体）

2. 将下载的文件放到：
   ```
   C:\Program Files\Tesseract-OCR\tessdata\
   ```

---

## 🚀 使用方法

### 方法一：运行 Python 脚本（推荐）

```bash
cd "d:\新建文件夹\仪度六壬择日\yiduluren\zongmen"
python extract_pdf_page.py
```

**脚本会自动：**
1. 检查依赖是否安装
2. 尝试直接提取文本（快速）
3. 如果失败，则提取为图片并进行 OCR 识别
4. 保存结果到 `pdf_extract` 目录

**输出文件：**
- `page_290.png` - 第 290 页的图片
- `page_290_ocr.txt` - OCR 识别的文本
- `page_290_direct.txt` - 直接提取的文本（如果有）

### 方法二：手动分步操作

#### 2.1 提取 PDF 页面为图片

```bash
python -c "from pdf2image import convert_from_path; images = convert_from_path(r'd:\新建文件夹\仪度六壬择日\yiduluren\[图解六壬大全。第 2 部。吉凶占断].许颐平。扫描版 [minxue.net].pdf', first_page=290, last_page=290, dpi=300); images[0].save(r'zongmen\pdf_extract\page_290.png')"
```

#### 2.2 进行 OCR 识别

```bash
python -c "import pytesseract; from PIL import Image; text = pytesseract.image_to_string(Image.open(r'zongmen\pdf_extract\page_290.png'), lang='chi_sim'); print(text)"
```

#### 2.3 保存识别结果

```bash
python -c "import pytesseract; from PIL import Image; text = pytesseract.image_to_string(Image.open(r'zongmen\pdf_extract\page_290.png'), lang='chi_sim'); open(r'zongmen\pdf_extract\page_290_ocr.txt', 'w', encoding='utf-8').write(text)"
```

---

## 📊 输出示例

### 提取的图片
```
pdf_extract/
└── page_290.png          (PNG 格式，300 DPI，约 2000x3000 像素)
```

### 识别的文本
```
pdf_extract/
└── page_290_ocr.txt      (UTF-8 编码，纯文本)
```

**文本内容示例：**
```
三光课

三光课者，谓干支上神得旺相，又三传皆阳...

【构成条件】
1. 干支上神旺相
2. 三传纯一（纯阳、纯阴或纯五行）

【吉凶判断】
大抵此课最吉，凡占皆遂...
```

---

## 🔧 高级功能

### 1. 调整 OCR 识别语言

如果识别的是繁体中文，修改脚本中的语言参数：

```python
# 在 extract_pdf_page.py 中
lang='chi_tra+eng'  # 繁体中文 + 英文
```

### 2. 提高识别准确率

#### 方法 A：提高 DPI
```python
# 修改 DPI 参数（默认 300）
images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=600)
```
更高的 DPI（如 600）可以提高识别准确率，但文件会更大。

#### 方法 B：图片增强
脚本已包含图片增强功能，会自动：
- 转换为灰度图
- 增强对比度
- 增强亮度
- 锐化

#### 方法 C：手动校对
OCR 识别后，人工校对并保存为：
```
page_290_corrected.txt
```

### 3. 批量提取多页

修改脚本，批量提取"64 课经"所有章节：

```python
# 批量提取第 280-350 页
for page in range(280, 351):
    extract_page_as_image(PDF_FILE, page, f"page_{page}.png")
    perform_ocr(f"page_{page}.png", f"page_{page}_ocr.txt")
```

---

## ⚠️ 常见问题

### Q1: `pdf2image` 安装失败

**错误信息：**
```
Unable to find poppler
```

**解决：** 需要安装 Poppler（PDF 渲染库）

**Windows 安装：**
1. 下载：http://blog.alivate.com.au/poppler-windows/
2. 下载 `poppler-xx.x.x_x64.7z`
3. 解压到：`C:\Program Files\poppler`
4. 添加环境变量：`C:\Program Files\poppler\Library\bin`

### Q2: Tesseract 识别率很低

**可能原因：**
1. 扫描质量差
2. 字体特殊
3. 页面有噪点

**解决方法：**
- 使用图片增强功能
- 提高 DPI 到 600
- 人工校对

### Q3: 无法识别中文

**原因：** 中文语言包未安装

**解决：**
```bash
# 检查语言包
tesseract --list-langs

# 如果没有 chi_sim，下载并复制到：
# C:\Program Files\Tesseract-OCR\tessdata\chi_sim.traineddata
```

### Q4: PDF 文件路径有空格

**错误：** 文件路径包含空格导致失败

**解决：** 使用原始字符串（在 Python 字符串前加 `r`）
```python
PDF_FILE = r"d:\路径\文件名.pdf"
```

---

## 📝 使用示例

### 完整流程示例

```bash
# 1. 进入目录
cd "d:\新建文件夹\仪度六壬择日\yiduluren\zongmen"

# 2. 运行脚本
python extract_pdf_page.py

# 3. 查看输出
dir pdf_extract

# 4. 查看识别结果
type pdf_extract\page_290_ocr.txt
```

### 在 Python 代码中调用

```python
from extract_pdf_page import extract_page_as_image, perform_ocr

# 提取图片
image_path = extract_page_as_image(
    pdf_path=r"d:\新建文件夹\仪度六壬择日\yiduluren\[图解六壬大全。第 2 部。吉凶占断].许颐平。扫描版 [minxue.net].pdf",
    page_num=290,
    output_path=r"pdf_extract\page_290.png",
    dpi=300
)

# OCR 识别
text = perform_ocr(
    image_path=image_path,
    output_txt=r"pdf_extract\page_290_ocr.txt",
    lang='chi_sim+eng'
)

print(text)
```

---

## 🎯 针对本项目的优化建议

### 1. 提取后直接用于对比分析

提取第 290 页后，立即进行对比分析：

```python
# 提取
text = extract_and_ocr()

# 保存到对比分析文件
with open('三光课_图解版.txt', 'w', encoding='utf-8') as f:
    f.write(text)

# 调用 Qwen Max API 进行对比
from qwen_analysis import compare_versions
compare_versions('原著版', '图解版')
```

### 2. 建立 64 课经完整文本库

批量提取所有课目：

```python
# 64 课经页码范围
for page in range(280, 350):
    extract_page(page)
    
# 整理成结构化数据
create_64_ke_database()
```

### 3. 与 720 课例匹配

提取后，更新标准化数据库：

```python
# 更新三光课数据
update_san_guang_data('图解版内容')

# 重新匹配 720 课例
match_720_ke_li()
```

---

## 📚 相关资源

### 官方文档
- Tesseract-OCR: https://tesseract-ocr.github.io/
- pdf2image: https://github.com/Belval/pdf2image
- Pillow: https://pillow.readthedocs.io/

### 中文教程
- Tesseract-OCR 中文文档：https://www.cnblogs.com/...
- Python PDF 处理：https://zhuanlan.zhihu.com/...

### 六壬资料
- 《六壬大全》原著电子版
- 720 课例数据库

---

## ✅ 检查清单

在开始之前，请确认：

- [ ] Python 3.8+ 已安装
- [ ] pdf2image 已安装
- [ ] pytesseract 已安装
- [ ] Pillow 已安装
- [ ] Tesseract-OCR 引擎已安装
- [ ] 中文语言包已安装
- [ ] PDF 文件路径正确
- [ ] 输出目录有写入权限

---

**准备就绪！开始提取吧！** 🚀

如有问题，请查看"常见问题"部分或联系技术支持。
