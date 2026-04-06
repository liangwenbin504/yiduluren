#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 PDF 课经提取引擎

功能：
1. 从《白话大六壬全书》PDF 提取 64 课经
2. 识别课名、原文、断语
3. 结构化存储
"""

import re
import os
import json

# 尝试导入 PDF 处理库
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("警告：未安装 PyMuPDF，请先安装：pip install PyMuPDF")


class PDFKeJingExtractor:
    """PDF 课经提取器"""
    
    def __init__(self, pdf_path):
        """
        初始化提取器
        
        :param pdf_path: PDF 文件路径
        """
        self.pdf_path = pdf_path
        self.ke_jing_data = {}
        
        if not PDF_AVAILABLE:
            raise ImportError("PyMuPDF 未安装")
    
    def extract_text(self):
        """从 PDF 提取文本"""
        doc = fitz.open(self.pdf_path)
        full_text = ""
        
        for page in doc:
            text = page.get_text()
            full_text += text + "\n"
        
        doc.close()
        return full_text
    
    def parse_ke_jing(self, text):
        """
        解析课经内容
        
        :param text: PDF 提取的文本
        :return: 课经数据字典
        """
        ke_jing_list = []
        
        # 课经识别模式
        # 示例：第 X 课 XXX 课
        ke_pattern = r'(?:第 [零一二三四五六七八九十百\d]+课\s*)?([\u4e00-\u9fa5]{2,4}课)'
        
        # 原文识别模式
        desc_pattern = r'(?:【原文】|原文：?|课曰：?|断曰：?)(.*?)(?:【|\n\n|断语|象曰|$)'
        
        # 断语识别模式
        judgment_pattern = r'(?:【断语】|断语：?|断曰：?|象曰：?)(.*?)(?:【|\n\n|第 \d+ 课|$)'
        
        # 查找所有课名
        ke_matches = re.finditer(ke_pattern, text, re.DOTALL)
        ke_positions = [(m.start(), m.end(), m.group(1)) for m in ke_matches]
        
        # 提取每课内容
        for i, (start, end, ke_name) in enumerate(ke_positions):
            # 确定本课结束位置（下一课开始）
            if i < len(ke_positions) - 1:
                next_start = ke_positions[i + 1][0]
            else:
                next_start = len(text)
            
            # 提取课文内容
            ke_text = text[end:next_start]
            
            # 提取原文
            desc_match = re.search(desc_pattern, ke_text, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # 提取断语
            judgment_match = re.search(judgment_pattern, ke_text, re.DOTALL)
            judgment = judgment_match.group(1).strip() if judgment_match else ""
            
            # 添加到列表
            ke_jing_list.append({
                'ke_name': ke_name,
                'description': description,
                'judgment': judgment,
                'raw_text': ke_text[:500]  # 保留部分原文用于分析
            })
        
        return ke_jing_list
    
    def extract_all(self):
        """提取所有课经"""
        print(f"正在从 PDF 提取课经：{self.pdf_path}")
        
        # 提取文本
        text = self.extract_text()
        print(f"提取文本长度：{len(text)}")
        
        # 解析课经
        ke_jing_list = self.parse_ke_jing(text)
        print(f"识别到课经数量：{len(ke_jing_list)}")
        
        # 存储数据
        for ke_info in ke_jing_list:
            ke_name = ke_info['ke_name']
            self.ke_jing_data[ke_name] = {
                'ke_name': ke_name,
                'ke_type': self._guess_ke_type(ke_name),
                'features': {},
                'description': ke_info['description'],
                'judgment': ke_info['judgment'],
                'examples': [],
                'source': '白话大六壬全书'
            }
        
        return self.ke_jing_data
    
    def _guess_ke_type(self, ke_name):
        """根据课名猜测课体"""
        if '涉害' in ke_name:
            return '涉害法'
        elif '遥克' in ke_name:
            return '遥克法'
        elif '昴星' in ke_name:
            return '昴星法'
        elif '别责' in ke_name or '八专' in ke_name:
            return '别责法'
        elif '伏吟' in ke_name:
            return '伏吟法'
        elif '反吟' in ke_name:
            return '反吟法'
        elif '贼克' in ke_name or '元首' in ke_name or '重审' in ke_name:
            return '贼克法'
        else:
            return '特殊课'
    
    def save_to_json(self, output_path='data/64_ke_jing.json'):
        """保存到 JSON 文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.ke_jing_data, f, ensure_ascii=False, indent=2)
        
        print(f"已保存到：{output_path}")
        return output_path


def extract_from_pdf(pdf_path):
    """
    从 PDF 提取课经的便捷函数
    
    :param pdf_path: PDF 文件路径
    :return: 课经数据
    """
    extractor = PDFKeJingExtractor(pdf_path)
    data = extractor.extract_all()
    extractor.save_to_json()
    return data


if __name__ == '__main__':
    # 测试
    pdf_file = "白话大六壬全书（有目录）.pdf"
    if os.path.exists(pdf_file):
        try:
            data = extract_from_pdf(pdf_file)
            print(f"\n提取成功！共 {len(data)} 课")
            for ke_name in list(data.keys())[:5]:
                print(f"  - {ke_name}")
        except Exception as e:
            print(f"提取失败：{e}")
    else:
        print(f"PDF 文件不存在：{pdf_file}")
        print("请确保 PDF 文件在项目根目录下")
