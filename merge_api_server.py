#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并 API 服务器文件的脚本
"""

import os

# 读取原始文件
with open('api_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 要插入的导出 API 代码
export_api_code = """

@app.route('/api/export/docx', methods=['POST'])
def export_docx():
    \"\"\"
    导出 docx 格式文档 - 使用模板
    
    参数:
        mountain: 坐山
        xiangshan: 向山
        four_pillars: 四柱信息 (dict: year, month, day, hour)
        dates: 日期列表 (list: [{date, hour, score}])
        evaluation: 评价文本
        title_type: 标题类型 (如"安葬吉日"、"立碑吉日"等)
    
    返回:
        JSON: {success: bool, file_path: str, filename: str, error: str}
    \"\"\"
    try:
        from export_docx import export_docx_document
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '未提供数据'
            })
        
        # 准备导出数据
        export_data = {
            'title': data.get('title_type', '擇日課單'),
            'zuoshan': data.get('mountain', ''),
            'xiangshan': data.get('xiangshan', ''),
            'four_pillars': data.get('four_pillars', {}),
            'dates': data.get('dates', []),
            'evaluation': data.get('evaluation', '')
        }
        
        # 调用导出函数
        result = export_docx_document(export_data)
        
        if result['success']:
            # 返回文件下载路径（相对路径）
            return jsonify({
                'success': True,
                'file_path': result['file_path'],
                'filename': result['filename'],
                'download_url': f"/api/export/download/{result['filename']}"
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '导出失败'),
                'detail': result.get('detail', '')
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })


@app.route('/api/export/download/<filename>', methods=['GET'])
def download_file(filename):
    \"\"\"
    下载导出的文件
    \"\"\"
    from flask import send_file
    import os
    
    file_path = os.path.join(os.path.dirname(__file__), filename)
    
    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'error': '文件不存在'
        }), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

"""

# 在 if __name__ == '__main__':之前插入
if "if __name__ == '__main__':" in content:
    content = content.replace(
        "if __name__ == '__main__':",
        export_api_code + "\nif __name__ == '__main__':"
    )
    
    # 保存合并后的文件
    with open('api_server_merged.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 文件合并成功！")
    print("📄 新文件：api_server_merged.py")
else:
    print("❌ 未找到 if __name__ == '__main__': 语句")
