# -*- coding: utf-8 -*-
from docx import Document

doc = Document(r'd:\新建文件夹\仪度六壬择日\yiduluren\择日课单_20260330_091220.docx')

html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>择日课单</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', 'SimSun', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.8;
            background: #fff;
        }
        h1 { text-align: center; color: #c00; border-bottom: 2px solid #c00; padding-bottom: 10px; }
        h2 { color: #333; border-left: 4px solid #c00; padding-left: 10px; margin-top: 20px; }
        h3 { color: #555; }
        .highlight { background: #fffde7; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .good { color: green; font-weight: bold; }
        .normal { color: #666; }
        table { border-collapse: collapse; width: 100%; margin: 15px 0; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background: #f5f5f5; }
        .sizhu { display: flex; justify-content: space-around; background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .sizhu-item { text-align: center; }
        .sizhu-item .label { font-size: 12px; color: #666; }
        .sizhu-item .value { font-size: 24px; font-weight: bold; color: #c00; }
        .score { font-size: 48px; color: #c00; text-align: center; font-weight: bold; }
        hr { border: none; border-top: 1px dashed #ccc; margin: 20px 0; }
    </style>
</head>
<body>
'''

for para in doc.paragraphs:
    text = para.text.strip()
    if not text:
        continue
    
    if '吉课' in text and len(text) < 10:
        html_content += f'<h1>{text}</h1>\n'
    elif text.startswith('【') and text.endswith('】'):
        html_content += f'<h2>{text}</h2>\n'
    elif '◆' in text:
        html_content += f'<h3>{text}</h3>\n'
    elif text.startswith('四柱：'):
        html_content += '<div class="sizhu">\n'
        parts = text.replace('四柱：', '').split()
        for p in parts:
            html_content += f'<div class="sizhu-item"><div class="label">柱</div><div class="value">{p}</div></div>\n'
        html_content += '</div>\n'
    elif '吉' in text[:5] or '平' in text[:5]:
        if '吉' in text[:5]:
            html_content += f'<p class="highlight"><span class="good">吉</span> - {text}</p>\n'
        else:
            html_content += f'<p class="highlight"><span class="normal">平</span> - {text}</p>\n'
    elif '综合评分' in text:
        import re
        match = re.search(r'(\d+)分', text)
        if match:
            score = match.group(1)
            html_content += f'<p class="score">{score}分</p>\n'
        html_content += f'<p>{text}</p>\n'
    else:
        html_content += f'<p>{text}</p>\n'

html_content += '</body></html>'

with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\择日课单_20260330_091220.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('HTML文件已生成！')
