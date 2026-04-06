#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试当前排盘数据
"""

import requests
import json
from datetime import datetime

def test_current_paipan():
    """测试当前排盘数据"""
    
    # 获取当前日期时间
    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    
    print("=" * 60)
    print(f"当前日期时间: {year}年{month}月{day}日{hour}时")
    print("=" * 60)
    
    # 获取四柱
    sizhu_url = f"http://localhost:5000/api/sizhu?year={year}&month={month}&day={day}&hour={hour}"
    sizhu_response = requests.get(sizhu_url)
    sizhu_data = sizhu_response.json()
    
    if sizhu_data.get('success'):
        print(f"\n四柱信息:")
        print(f"  年柱: {sizhu_data['sizhu']['yearPillar']}")
        print(f"  月柱: {sizhu_data['sizhu']['monthPillar']}")
        print(f"  日柱: {sizhu_data['sizhu']['dayPillar']}")
        print(f"  时柱: {sizhu_data['sizhu']['hourPillar']}")
        
        day_gan = sizhu_data['sizhu']['dayGan']
        day_zhi = sizhu_data['sizhu']['dayZhi']
        
        print(f"\n日干支: {day_gan}{day_zhi}")
        
        # 获取天地盘
        # 月将根据月份计算
        yuejiang_map = {
            1: '丑', 2: '子', 3: '亥', 4: '戌', 5: '酉', 6: '申',
            7: '未', 8: '午', 9: '巳', 10: '辰', 11: '卯', 12: '寅'
        }
        yue_jiang = yuejiang_map[month]
        
        # 时辰地支
        dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        shichen_index = (hour + 1) // 2 % 12
        shi_chen = dizhi[shichen_index]
        
        print(f"月将: {yue_jiang}")
        print(f"时辰: {shi_chen}")
        
        tiandi_url = f"http://localhost:5000/api/daliuren/tiandi_pan?yuejiang={yue_jiang}&shichen={shi_chen}"
        tiandi_response = requests.get(tiandi_url)
        tiandi_data = tiandi_response.json()
        
        if tiandi_data.get('success'):
            print(f"\n天地盘:")
            print(f"  地盘: {tiandi_data['di_pan']}")
            print(f"  天盘: {tiandi_data['tian_pan']}")
            print(f"\n天地对应:")
            for di, tian in tiandi_data['tiandi_duiying'].items():
                print(f"  地盘{di} → 天盘{tian}")
            
            # 获取四课
            sike_url = "http://localhost:5000/api/daliuren/si_ke"
            sike_data = {
                "ri_gan": day_gan,
                "ri_zhi": day_zhi,
                "yuejiang": yue_jiang,
                "shichen": shi_chen
            }
            sike_response = requests.post(sike_url, json=sike_data)
            sike_result = sike_response.json()
            
            if sike_result.get('success'):
                print(f"\n四课:")
                for ke in sike_result['si_ke']:
                    print(f"  {ke['name']}: 上神={ke['top']}, 下神={ke['bottom']}")
                
                # 获取三传
                sanchuan_url = "http://localhost:5000/api/daliuren/san_chuan"
                sanchuan_data = {
                    "ri_gan": day_gan,
                    "ri_zhi": day_zhi,
                    "yue_jiang": yue_jiang,
                    "shi_chen": shi_chen
                }
                sanchuan_response = requests.post(sanchuan_url, json=sanchuan_data)
                sanchuan_result = sanchuan_response.json()
                
                if sanchuan_result.get('success'):
                    print(f"\n三传:")
                    sanchuan = sanchuan_result['sanchuan']
                    print(f"  初传: {sanchuan['chuChuan']}")
                    print(f"  中传: {sanchuan['zhongChuan']}")
                    print(f"  末传: {sanchuan['moChuan']}")
                    print(f"  课体: {sanchuan['keTi']}")
                    print(f"  起法: {sanchuan['qiFa']}")
                    
                    # 验证三传
                    tiandi_duiying = tiandi_data['tiandi_duiying']
                    
                    print(f"\n三传验证:")
                    chu = sanchuan['chuChuan']
                    zhong = tiandi_duiying.get(chu, '?')
                    mo = tiandi_duiying.get(zhong, '?')
                    
                    print(f"  初传: {chu}")
                    print(f"  中传（初传作为地盘，其天盘）: {zhong}")
                    print(f"  末传（中传作为地盘，其天盘）: {mo}")
                    
                    if sanchuan['zhongChuan'] == zhong and sanchuan['moChuan'] == mo:
                        print("\n✅ 三传计算正确！")
                    else:
                        print(f"\n❌ 三传计算错误！")
                        print(f"  期望中传: {zhong}, 实际: {sanchuan['zhongChuan']}")
                        print(f"  期望末传: {mo}, 实际: {sanchuan['moChuan']}")
                else:
                    print(f"三传API调用失败: {sanchuan_result.get('error')}")
            else:
                print(f"四课API调用失败: {sike_result.get('error')}")
        else:
            print(f"天地盘API调用失败: {tiandi_data.get('error')}")
    else:
        print(f"四柱API调用失败: {sizhu_data.get('error')}")

if __name__ == "__main__":
    test_current_paipan()
