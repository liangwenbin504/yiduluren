# -*- coding: utf-8 -*-
"""
大六壬断案疏正PDF内容提取器
从PDF中提取每一课的内容并系统化整理
"""

import re
import PyPDF2
import json


class DuanAnPDFExtractor:
    """断案PDF提取器"""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.pdf = PyPDF2.PdfReader(pdf_path)
        self.page_count = len(self.pdf.pages)
        self.cases = []

    def extract_page(self, page_num):
        """提取指定页内容"""
        if 0 <= page_num < self.page_count:
            return self.pdf.pages[page_num].extract_text()
        return ""

    def extract_case_content(self, case_id, page_num):
        """提取单课内容"""
        content = self.extract_page(page_num)
        if not content:
            return None

        case = {
            'case_id': case_id,
            'page': page_num + 1,
            'content': content,
            'segments': self._parse_segments(content)
        }
        return case

    def _parse_segments(self, content):
        """解析内容分段"""
        segments = {}

        lines = content.split('\n')
        current_segment = None
        current_text = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if '邵先生曰' in line or '邵彦和曰' in line:
                if current_text:
                    segments[current_segment] = '\n'.join(current_text)
                current_segment = 'judgment'
                current_text = [line]
            elif '【评疏】' in line:
                if current_text:
                    segments[current_segment] = '\n'.join(current_text)
                current_segment = 'analysis'
                current_text = [line]
            elif '课体课格' in line or '课体课袼' in line:
                if current_text:
                    segments[current_segment] = '\n'.join(current_text)
                current_segment = 'keti'
                current_text = [line]
            elif '神煞' in line and len(line) < 20:
                if current_text:
                    segments[current_segment] = '\n'.join(current_text)
                current_segment = 'shensha'
                current_text = [line]
            else:
                current_text.append(line)

        if current_text and current_segment:
            segments[current_segment] = '\n'.join(current_text)

        return segments

    def extract_all_tianshi_cases(self):
        """提取天时类所有案例"""
        cases = []
        for i in range(23, 30):
            content = self.extract_page(i)
            if content and ('天时' in content or '祈雪' in content or '占晴' in content or '占雨' in content):
                case = {
                    'case_id': f'天时01·{i-22:03d}',
                    'page': i + 1,
                    'content': content,
                    'type': '天时'
                }
                cases.append(case)
        return cases

    def extract_category_cases(self, category_pages):
        """提取指定页码范围的案例"""
        cases = []
        for page_num in range(*category_pages):
            if page_num < self.page_count:
                content = self.extract_page(page_num)
                if content.strip():
                    cases.append({
                        'page': page_num + 1,
                        'content': content
                    })
        return cases

    def save_cases_to_json(self, cases, output_path):
        """保存案例到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    pdf_path = r'data\大六壬断案疏正.pdf'
    extractor = DuanAnPDFExtractor(pdf_path)

    print(f"PDF总页数: {extractor.page_count}")

    output_dir = r'data\断案疏正提取'

    print("\n开始提取天时类案例...")
    tianshi_cases = extractor.extract_all_tianshi_cases()
    print(f"提取到天时类案例: {len(tianshi_cases)} 个")

    print("\n天时类案例概要:")
    for case in tianshi_cases[:3]:
        print(f"\n案例 {case['case_id']} (第{case['page']}页):")
        content = case['content'][:500]
        print(content)
        print("...")

    return tianshi_cases


if __name__ == '__main__':
    main()