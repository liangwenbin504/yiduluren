#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档导出功能 - 四重保险版！
绝对确保印章图片是浮于文字上方！
"""

import os
import sys
import datetime
import traceback
import shutil

# 尝试导入win32com用于高级Word操作
try:
    import win32com.client as win32
    import pythoncom
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False
    print("⚠️  win32com不可用，无法导出文档")


def force_all_pictures_float_above_text(doc, word):
    """强制所有图片为浮于文字上方（绝对保险）"""
    print("    🔒 执行强制图片浮于文字上方...")
    
    # 1. 先处理所有嵌入型图片
    inline_count = doc.InlineShapes.Count
    print(f"      - 找到 {inline_count} 个嵌入型图片")
    for i in range(inline_count, 0, -1):
        try:
            inline_shape = doc.InlineShapes(i)
            if inline_shape.Type == 3:  # wdInlineShapePicture
                print(f"      - 转换嵌入型图片 {i} 为浮动型")
                shape = inline_shape.ConvertToShape()
                # 强制设置浮于文字上方
                shape.WrapFormat.Type = 3  # wdWrapFront
                shape.ZOrder(0)  # 最上层
                print(f"      - 图片 {i} 已强制设置为浮于文字上方")
        except Exception as e:
            print(f"      ⚠️  转换图片 {i} 时出错: {e}")
    
    # 2. 再确保所有浮动图片都是浮于文字上方
    shape_count = doc.Shapes.Count
    print(f"      - 找到 {shape_count} 个浮动图片")
    for i in range(1, shape_count + 1):
        try:
            shape = doc.Shapes(i)
            # 强制设置浮于文字上方
            shape.WrapFormat.Type = 3  # wdWrapFront
            shape.ZOrder(0)  # 最上层
            print(f"      - 浮动图片 {i} 已强制确认为浮于文字上方 (Type=3, ZOrder=0)")
        except Exception as e:
            print(f"      ⚠️  设置图片 {i} 时出错: {e}")
    
    print("    🔒 强制完成")


def export_docx_document(data):
    """导出择日课单为DOCX文档（四重保险版）"""
    # ====================================================
    # 超级明显的调试信息！！！
    # ====================================================
    print("=" * 80)
    print("🔥🔥🔥 这是四重保险版本！！！🔥🔥🔥")
    print("🔥🔥🔥 绝对确保印章浮于文字上方！🔥🔥🔥")
    print("=" * 80)
    
    if not WIN32COM_AVAILABLE:
        print("❌ win32com不可用，无法导出文档")
        return None
        
    try:
        print("📝 开始导出文档（四重保险版）...")
        
        # ========================================
        # 查找完美模板
        # ========================================
        template_files = [
            '完美模板.docx'
        ]
        
        template_path = None
        for template_file in template_files:
            candidate_path = os.path.join(os.path.dirname(__file__), template_file)
            if os.path.exists(candidate_path):
                template_path = candidate_path
                print(f"✅ 使用模板: {template_file}")
                break
        
        if not template_path:
            raise FileNotFoundError("未找到任何模板文件")
        
        # ========================================
        # 提取数据
        # ========================================
        title = data.get('title_type', data.get('title', '择日课单'))
        zuoshan = data.get('mountain', data.get('zuoshan', ''))
        xiangshan = data.get('xiangshan', '')
        
        four_pillars = data.get('four_pillars', {})
        year_pillar = four_pillars.get('year', '')
        month_pillar = four_pillars.get('month', '')
        day_pillar = four_pillars.get('day', '')
        hour_pillar = four_pillars.get('hour', '')
        
        daliuren_data = data.get('daliuren_data', {})
        yuejiang = daliuren_data.get('yueJiang', '')
        shichen = daliuren_data.get('shiChen', '')
        
        liuren_kege = ''
        if yuejiang or shichen:
            liuren_kege_parts = []
            if yuejiang:
                liuren_kege_parts.append(f'{yuejiang}将')
            if shichen:
                liuren_kege_parts.append(f'{shichen}时')
            liuren_kege = ' '.join(liuren_kege_parts)
        
        piyu = data.get('evaluation', '')
        piyu_lines = []
        if piyu:
            piyu_lines = [line.strip() for line in piyu.split('\n') if line.strip()]
        
        dates = data.get('dates', [])
        biji = ''
        if dates and len(dates) > 0:
            first_date = dates[0]
            date_str = first_date.get('date', '')
            hour_str = first_date.get('hour', '')
            score_str = first_date.get('score', '')
            if date_str:
                biji = f'参考日期：{date_str}'
                if hour_str:
                    biji += f' {hour_str}时'
                if score_str:
                    biji += f' 评分：{score_str}'
        
        diliishi = data.get('diliishi', '信林居士')
        date = datetime.datetime.now().strftime('%Y年%m月%d日')
        
        print(f"📌 导出数据 - 标题: {title}")
        
        # ========================================
        # 启动Word
        # ========================================
        print("📝 开始使用win32com编辑文档...")
        
        # 初始化 COM（多线程环境必须）
        try:
            pythoncom.CoInitialize()
            print("  - COM已初始化")
        except:
            pass
        
        app_prog_ids = [
            "Word.Application",
            "WPS.Application",
            "KWps.Application",
        ]
        
        word = None
        for prog_id in app_prog_ids:
            try:
                print(f"🔍 尝试启动: {prog_id}")
                word = win32.DispatchEx(prog_id)
                word.Visible = False
                word.DisplayAlerts = 0
                print(f"✅ 成功启动: {prog_id}")
                break
            except Exception as e:
                print(f"⚠️  启动 {prog_id} 失败: {e}")
                word = None
                continue
        
        if word is None:
            print("❌ 无法启动任何Office应用程序")
            return None
        
        try:
            # ========================================
            # 第一重保险：打开模板，先强制设置一次
            # ========================================
            print("🔒 第一重保险：打开模板...")
            doc = word.Documents.Open(os.path.abspath(template_path))
            force_all_pictures_float_above_text(doc, word)
            
            # ========================================
            # 清空文本
            # ========================================
            print("  - 清空文本内容（完全不动图片）...")
            para_count = doc.Paragraphs.Count
            print(f"  - 共有 {para_count} 个段落")
            
            for i in range(para_count, 0, -1):
                para = doc.Paragraphs(i)
                has_picture = False
                
                # 检查是否有嵌入型图片
                try:
                    for j in range(1, doc.InlineShapes.Count + 1):
                        try:
                            inline_shape = doc.InlineShapes(j)
                            if (inline_shape.Range.Start >= para.Range.Start and 
                                inline_shape.Range.End <= para.Range.End):
                                has_picture = True
                                break
                        except:
                            pass
                except:
                    pass
                
                # 检查是否有浮动图片锚点
                if not has_picture:
                    try:
                        for j in range(1, doc.Shapes.Count + 1):
                            try:
                                shape = doc.Shapes(j)
                                if shape.Anchor:
                                    anchor_para = shape.Anchor.Paragraphs(1)
                                    if anchor_para.Range.Start == para.Range.Start:
                                        has_picture = True
                                        break
                            except:
                                pass
                    except:
                        pass
                
                # 如果没有图片，就清空文本
                if not has_picture:
                    if para.Range.Text.strip() != '':
                        para.Range.Text = ''
            
            # ========================================
            # 第二重保险：清空文本后，再强制设置一次
            # ========================================
            print("🔒 第二重保险：清空后确认图片...")
            force_all_pictures_float_above_text(doc, word)
            
            # ========================================
            # 添加新内容
            # ========================================
            print("  - 添加新内容...")
            selection = word.Selection
            selection.HomeKey(Unit=6)
            
            def add_paragraph(text, font_size=16, alignment=2):
                selection.TypeText(text)
                selection.TypeParagraph()
                last_para = doc.Paragraphs(doc.Paragraphs.Count - 1)
                last_para.Alignment = alignment
                last_para.Range.Font.Name = "楷体"
                last_para.Range.Font.NameFarEast = "楷体"
                last_para.Range.Font.Size = font_size
            
            add_paragraph(title, font_size=46, alignment=1)
            add_paragraph("")
            add_paragraph("伏以，天地定位，山向合机；理气相通，福泽攸关。谨奉《穿山透地真传》之旨，依《仪度六壬选日要诀》之法，为孝眷择取立碑吉期，安妥先灵，庇荫后昆。")
            
            if zuoshan and xiangshan:
                add_paragraph(f"山向：{zuoshan}山{xiangshan}向")
            elif zuoshan:
                add_paragraph(f"山向：{zuoshan}山")
            
            if year_pillar and month_pillar and day_pillar and hour_pillar:
                add_paragraph(f"择取岁次{year_pillar}年{month_pillar}月{day_pillar}日{hour_pillar}时（干支：{year_pillar}年{month_pillar}月{day_pillar}日{hour_pillar}时）")
            
            if liuren_kege:
                add_paragraph(f"六壬课格：{liuren_kege}")
            
            if piyu_lines and len(piyu_lines) > 0:
                for line in piyu_lines:
                    add_paragraph(line)
            elif piyu:
                add_paragraph(f"批语：{piyu}")
            
            if biji:
                add_paragraph(f"{biji}")
            
            add_paragraph(f"{diliishi}沐手谨择", alignment=2)
            add_paragraph(f"日期：岁次{date}榖旦 勒石", alignment=2)
            
            # ========================================
            # 第三重保险：添加内容后，再强制设置一次
            # ========================================
            print("🔒 第三重保险：添加内容后确认图片...")
            force_all_pictures_float_above_text(doc, word)
            
            # ========================================
            # 保存
            # ========================================
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'择日课单_{timestamp}.docx'
            # 保存到系统下载文件夹
            downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            if not os.path.exists(downloads_dir):
                downloads_dir = os.path.dirname(__file__)
            output_path = os.path.join(downloads_dir, filename)
            
            print(f"  - 保存文档: {filename}")
            print(f"  - 保存路径: {output_path}")
            doc.SaveAs2(os.path.abspath(output_path), FileFormat=16)
            print("✅ 文档已保存")
            doc.Close(SaveChanges=False)
            print("✅ 文档已关闭")
            
        except Exception as e:
            print(f"⚠️  win32com操作失败: {e}")
            traceback.print_exc()
        finally:
            if word is not None:
                try:
                    word.Quit()
                    print("✅ Word已关闭")
                except:
                    pass
        
        print(f"✅ 文档导出成功: {filename}")
        
        # 兼容旧版本返回格式
        return {
            'success': True,
            'file_path': os.path.abspath(output_path),
            'filename': filename
        }
        
    except Exception as e:
        print(f"❌ 文档导出失败: {e}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    test_data = {
        'title_type': '立碑吉课',
        'mountain': '壬',
        'xiangshan': '丙',
        'four_pillars': {
            'year': '丙午',
            'month': '甲午',
            'day': '丙午',
            'hour': '甲午'
        },
        'daliuren_data': {
            'yueJiang': '巳',
            'shiChen': '午',
            'tianPan': {},
            'sike': [],
            'sanchuan': {}
        },
        'dates': [
            {
                'date': '2026-04-01',
                'hour': '午时',
                'score': '98'
            }
        ],
        'keti_list': ['元首课', '龙德课'],
        'evaluation': '此课大吉，主子孙昌盛，福禄双全。课体平稳，无大吉凶。'
    }
    
    result = export_docx_document(test_data)
    print(result)
