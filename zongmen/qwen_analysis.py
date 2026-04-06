"""
使用 Qwen Max API 进行 64 课文本对比分析
配置已更新，可直接运行
"""

from dashscope import Generation
import json
import os

# ========== 配置区域 ==========
# Qwen Max API Key
QWEN_API_KEY = '***REMOVED***'

# 输入文件
EXTRACTED_TEXT_PATH = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\baidu_ocr\sanguang_baidu_merged.txt'
ORIGINAL_TEXT_PATH = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\64_ke_original.txt'  # 原著文本（如有）

# 输出目录
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\qwen_analysis'
# ===========================================


def initialize_client():
    """初始化 Qwen 客户端"""
    import dashscope
    dashscope.api_key = QWEN_API_KEY
    print("✓ Qwen Max API 已初始化")
    return dashscope


def compare_texts_qwen(extracted_text, original_text=None):
    """
    使用 Qwen Max 进行文本对比
    
    参数：
        extracted_text: 提取的文本
        original_text: 原著文本（可选）
    
    返回：
        对比分析结果
    """
    prompt = f"""
请对以下大六壬 64 课文本进行专业分析：

【提取文本】
{extracted_text[:3000]}  # 限制长度

{'【原著文本】\\n' + original_text[:3000] if original_text else '（暂无原著文本对比）'}

请完成以下分析任务：

1. **内容结构分析**
   - 识别课名
   - 提取核心定义
   - 列出关键术语

2. **文本质量评估**
   - OCR 识别准确率评估
   - 指出可能的识别错误
   - 建议校正的内容

3. **知识点提取**
   - 提取重要概念
   - 归纳占断规则
   - 整理吉凶判断

4. **差异分析**（如有原著）
   - 文字差异
   - 注释增减
   - 解释变化

请以 JSON 格式输出分析结果。
"""
    
    try:
        response = Generation.call(
            model='qwen-max',
            prompt=prompt,
            temperature=0.1,
            max_tokens=2000
        )
        
        if response.status_code == 200:
            return response.output.text
        else:
            print(f"✗ API 调用失败：{response.code}")
            return None
            
    except Exception as e:
        print(f"✗ 错误：{e}")
        return None


def analyze_single_ke(ke_name, ke_text):
    """
    分析单个课
    
    参数：
        ke_name: 课名
        ke_text: 课文内容
    
    返回：
        分析结果
    """
    prompt = f"""
请分析大六壬 64 课中的"{ke_name}"课：

【课文内容】
{ke_text}

请提供以下分析：

1. **课体特征**
   - 五行属性
   - 吉凶性质
   - 特殊格局

2. **核心定义**
   - 用神特点
   - 日辰关系
   - 天将配置

3. **占断要点**
   - 主要断语
   - 应用场景
   - 注意事项

4. **相关课例**
   - 典型课例特征
   - 匹配建议

请以结构化格式输出。
"""
    
    try:
        response = Generation.call(
            model='qwen-max',
            prompt=prompt,
            temperature=0.1,
            max_tokens=1500
        )
        
        if response.status_code == 200:
            return response.output.text
        else:
            return None
            
    except Exception as e:
        print(f"错误：{e}")
        return None


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("Qwen Max API 64 课分析工具")
    print("=" * 70)
    
    # 初始化
    initialize_client()
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 读取提取的文本
    if os.path.exists(EXTRACTED_TEXT_PATH):
        with open(EXTRACTED_TEXT_PATH, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
        print(f"✓ 已读取提取文本（{len(extracted_text)} 字符）")
    else:
        print(f"✗ 提取文本不存在：{EXTRACTED_TEXT_PATH}")
        return
    
    # 检查是否有原著文本
    original_text = None
    if os.path.exists(ORIGINAL_TEXT_PATH):
        with open(ORIGINAL_TEXT_PATH, 'r', encoding='utf-8') as f:
            original_text = f.read()
        print(f"✓ 已读取原著文本（{len(original_text)} 字符）")
    else:
        print("⚠ 未找到原著文本，将仅进行内容分析")
    
    # 执行对比分析
    print("\n正在调用 Qwen Max API 进行分析...")
    analysis_result = compare_texts_qwen(extracted_text, original_text)
    
    if analysis_result:
        # 保存结果
        output_path = os.path.join(OUTPUT_DIR, '64_ke_analysis_result.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(analysis_result)
        
        print(f"✓ 分析完成，结果已保存：{output_path}")
        print("\n" + "=" * 70)
        print("分析预览（前 500 字符）：")
        print("=" * 70)
        print(analysis_result[:500])
        print("=" * 70)
    else:
        print("✗ 分析失败")
    
    print("\n" + "=" * 70)
    print("Qwen Max API 分析完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
