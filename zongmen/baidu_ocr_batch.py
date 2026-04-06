"""
使用百度 OCR 批量识别三光课内容（292-297 页）
高精度版，支持古籍文字识别

配置说明：
1. 将下面的 APP_ID、API_KEY、SECRET_KEY 替换为您的实际密钥
2. 运行脚本即可批量识别
"""

from aip import AipOcr
import os
import json

# ========== 配置区域（请修改这里）==========
# 从百度 OCR 控制台获取的密钥（2026-03-21 更新）
APP_ID = '122486396'
API_KEY = '***REMOVED***'
SECRET_KEY = 'wdrSqpnJOtkzVrRpZobYybqidSBdUPNM'

# 图片目录（64 课全书）
INPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\images'
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\baidu_ocr'

# 页码范围（全书 64 课内容）
PAGE_START = 207
PAGE_END = 610
# ===========================================


def check_config():
    """检查配置是否正确"""
    if APP_ID == '您的 APP_ID（client_id）':
        print("=" * 70)
        print("❌ 错误：请先配置 API 密钥！")
        print("=" * 70)
        print("\n配置步骤：")
        print("1. 打开百度 OCR 控制台：https://console.bce.baidu.com/ai/")
        print("2. 找到您的应用")
        print("3. 复制 APP_ID、API_KEY、SECRET_KEY")
        print("4. 修改本文件中的配置")
        print("=" * 70)
        return False
    return True


def create_output_dir():
    """创建输出目录"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✓ 输出目录：{OUTPUT_DIR}")


def recognize_single_image(client, image_path):
    """
    识别单张图片（高精度版）
    
    参数：
        client: AipOcr 客户端
        image_path: 图片路径
    
    返回：
        识别结果字典
    """
    with open(image_path, 'rb') as f:
        image = f.read()
    
    # 调用高精度识别接口
    result = client.basicAccurate(image, {
        'recognize_granularity': 'big',  # 定位字符位置
        'probability': 'true',  # 返回置信度
    })
    
    return result


def save_result(result, output_path):
    """
    保存识别结果
    
    参数：
        result: 识别结果
        output_path: 输出文件路径
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        if 'words_result' in result:
            for word in result['words_result']:
                f.write(word['words'] + '\n')
        
        # 同时保存 JSON 格式（包含位置信息）
        json_path = output_path.replace('.txt', '.json')
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(result, jf, ensure_ascii=False, indent=2)


def batch_recognize():
    """批量识别主函数"""
    print("\n" + "=" * 70)
    print("百度 OCR 批量识别工具")
    print("=" * 70)
    
    # 检查配置
    if not check_config():
        return
    
    # 创建输出目录
    create_output_dir()
    
    # 初始化客户端
    print("\n正在初始化百度 OCR 客户端...")
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    
    # 测试连接
    try:
        test_img_path = os.path.join(INPUT_DIR, f'page_{PAGE_START}.png')
        if os.path.exists(test_img_path):
            with open(test_img_path, 'rb') as f:
                test_img = f.read()
            client.basicAccurate(test_img, {'recognize_granularity': 'big'})
            print("✓ 连接百度 OCR 成功！")
    except Exception as e:
        print(f"✗ 连接失败：{e}")
        print("\n请检查：")
        print("1. APP_ID、API_KEY、SECRET_KEY 是否正确")
        print("2. 网络连接是否正常")
        print("3. 账户是否有可用额度")
        return
    
    print("\n" + "=" * 70)
    print(f"开始批量识别（第 {PAGE_START}-{PAGE_END} 页）")
    print("=" * 70)
    
    results = []
    
    for page_num in range(PAGE_START, PAGE_END + 1):
        img_path = os.path.join(INPUT_DIR, f'page_{page_num}.png')
        
        if not os.path.exists(img_path):
            print(f"\n✗ 第 {page_num} 页：图片不存在")
            results.append({
                'page': page_num,
                'success': False,
                'error': '图片不存在'
            })
            continue
        
        print(f"\n正在识别第 {page_num} 页...")
        
        try:
            # 识别
            result = recognize_single_image(client, img_path)
            
            # 保存结果
            output_txt = os.path.join(OUTPUT_DIR, f'page_{page_num}.txt')
            save_result(result, output_txt)
            
            # 统计信息
            word_count = len(result.get('words_result', []))
            
            print(f"  ✓ 识别成功")
            print(f"    文字行数：{word_count}")
            print(f"    保存位置：{output_txt}")
            
            results.append({
                'page': page_num,
                'success': True,
                'word_count': word_count,
                'output': output_txt
            })
            
        except Exception as e:
            print(f"  ✗ 识别失败：{e}")
            results.append({
                'page': page_num,
                'success': False,
                'error': str(e)
            })
    
    # 生成摘要报告
    print("\n" + "=" * 70)
    print("识别完成摘要")
    print("=" * 70)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    print(f"总页数：{total}")
    print(f"成功：{successful} 页")
    print(f"失败：{failed} 页")
    
    if failed > 0:
        print(f"\n失败的页码：{[r['page'] for r in results if not r['success']]}")
    
    print("\n各页识别情况：")
    for r in results:
        if r['success']:
            print(f"  第 {r['page']} 页：✓ ({r['word_count']} 行)")
        else:
            print(f"  第 {r['page']} 页：✗ ({r.get('error', '未知错误')})")
    
    # 生成合并文件
    merged_path = os.path.join(OUTPUT_DIR, 'sanguang_baidu_merged.txt')
    with open(merged_path, 'w', encoding='utf-8') as f:
        f.write("# 三光课内容（百度 OCR 高精度识别）\n\n")
        f.write(f"识别时间：2026-03-21\n")
        f.write(f"页码范围：{PAGE_START}-{PAGE_END}\n")
        f.write(f"识别引擎：百度 OCR 高精度版\n\n")
        f.write("=" * 70 + "\n\n")
        
        for r in results:
            if r['success']:
                f.write(f"## 第 {r['page']} 页\n\n")
                txt_path = os.path.join(OUTPUT_DIR, f'page_{r["page"]}.txt')
                with open(txt_path, 'r', encoding='utf-8') as tf:
                    f.write(tf.read())
                f.write("\n" + "=" * 70 + "\n\n")
    
    print(f"\n合并文件已保存：{merged_path}")
    print("\n" + "=" * 70)
    print("批量识别完成！")
    print("=" * 70)


if __name__ == "__main__":
    batch_recognize()
