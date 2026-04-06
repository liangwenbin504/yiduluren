#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
宗门九课起课法 - HTTP API 服务器（独立版本）
不依赖外部模块，所有功能内嵌
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi


# ========== 内嵌六亲计算功能 ==========
class SimpleLiuQin:
    """简化的六亲计算器"""
    
    # 十干五行
    STEM_WUXING = {
        '甲': '木', '乙': '木',
        '丙': '火', '丁': '火',
        '戊': '土', '己': '土',
        '庚': '金', '辛': '金',
        '壬': '水', '癸': '水'
    }
    
    # 地支五行
    BRANCH_WUXING = {
        '子': '水', '亥': '水',
        '寅': '木', '卯': '木',
        '巳': '火', '午': '火',
        '申': '金', '酉': '金',
        '丑': '土', '辰': '土', '未': '土', '戌': '土'
    }
    
    # 六亲关系
    LIUQIN_MAP = {
        ('木', '木'): '兄', ('木', '火'): '子', ('木', '土'): '财', ('木', '金'): '鬼', ('木', '水'): '父',
        ('火', '木'): '父', ('火', '火'): '兄', ('火', '土'): '子', ('火', '金'): '财', ('火', '水'): '鬼',
        ('土', '木'): '鬼', ('土', '火'): '父', ('土', '土'): '兄', ('土', '金'): '子', ('土', '水'): '财',
        ('金', '木'): '财', ('金', '火'): '鬼', ('金', '土'): '父', ('金', '金'): '兄', ('金', '水'): '子',
        ('水', '木'): '子', ('水', '火'): '财', ('水', '土'): '鬼', ('水', '金'): '父', ('水', '水'): '兄',
    }
    
    def get_liuqin(self, ri_gan: str, branch: str) -> str:
        """计算六亲"""
        gan_wuxing = self.STEM_WUXING.get(ri_gan, '木')
        branch_wuxing = self.BRANCH_WUXING.get(branch, '木')
        return self.LIUQIN_MAP.get((gan_wuxing, branch_wuxing), '兄')


# ========== 内嵌旬遁和空亡计算功能 ==========
def get_xun_shou(ri_gan: str, ri_zhi: str):
    """
    计算日干支的旬首和空亡（旬遁法）
    
    :param ri_gan: 日干
    :param ri_zhi: 日支
    :return: (旬首地支，空亡地支列表)
    """
    stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    gan_index = stems.index(ri_gan)
    zhi_index = branches.index(ri_zhi)
    
    # 计算 60 甲子序号
    ganzhi_index = (gan_index * 6 - zhi_index * 5) % 60
    if ganzhi_index < 0:
        ganzhi_index += 60
    
    # 旬首序号
    xun_shou_index = (ganzhi_index // 10) * 10
    
    # 旬首地支
    xun_shou_zhi = branches[xun_shou_index % 12]
    
    # 计算空亡
    kong_wang_index1 = (xun_shou_index % 12 + 10) % 12
    kong_wang_index2 = (xun_shou_index % 12 + 11) % 12
    kong_wang = [branches[kong_wang_index1], branches[kong_wang_index2]]
    
    return xun_shou_zhi, kong_wang


def get_stem_for_branch(branch: str, ri_gan: str, ri_zhi: str) -> str:
    """计算遁干（旬遁法）"""
    stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    _, xun_shou_zhi, _ = get_xun_shou(ri_gan, ri_zhi)
    xun_index = branches.index(xun_shou_zhi)
    branch_index = branches.index(branch)
    distance = (branch_index - xun_index) % 12
    stem_index = distance % 10
    
    return stems[stem_index]


def is_kong_wang(branch: str, ri_gan: str, ri_zhi: str) -> bool:
    """判断是否空亡"""
    _, kong_wang = get_xun_shou(ri_gan, ri_zhi)
    return branch in kong_wang


# ========== API 处理器 ==========
class ZongMenAPIHandler(SimpleHTTPRequestHandler):
    """宗门九课 API 处理器"""
    
    def __init__(self, *args, **kwargs):
        # 动态导入计算器（每次请求都重新加载）
        import importlib.util
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        src_engine_dir = os.path.join(base_dir, '..', 'src', 'engine')
        src_dir = os.path.join(base_dir, '..', 'src')
        
        if src_engine_dir not in sys.path:
            sys.path.insert(0, src_engine_dir)
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        
        # 加载 sike_sanchuan_engine
        sike_path = os.path.join(src_engine_dir, 'sike_sanchuan_engine.py')
        spec = importlib.util.spec_from_file_location('sike_sanchuan_engine', sike_path)
        sike_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sike_module)
        SiKeSanChuanCalculator = sike_module.SiKeSanChuanCalculator
        
        self.calculator = SiKeSanChuanCalculator()
        self.liuqin_calc = SimpleLiuQin()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.endswith('.html'):
            self.serve_html_file(parsed_path.path)
        elif parsed_path.path == '/api/qike':
            self.handle_qike_api(parsed_path.query)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/qike':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            if 'application/json' in self.headers.get('Content-Type', ''):
                params = json.loads(post_data)
            else:
                params = dict(parse_qs(post_data))
                params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            
            self.handle_qike_api_post(params)
        else:
            self.send_error(404)
    
    def serve_html_file(self, path):
        """服务 HTML 文件"""
        file_path = os.path.join(os.path.dirname(__file__), path.lstrip('/'))
        if os.path.exists(file_path):
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)
    
    def send_json_response(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def handle_qike_api(self, query_string):
        """处理起课 API 请求（GET）"""
        params = dict(parse_qs(query_string))
        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        self.handle_qike_logic(params)
    
    def handle_qike_api_post(self, params):
        """处理起课 API 请求（POST）"""
        self.handle_qike_logic(params)
    
    def handle_qike_logic(self, params):
        """处理起课逻辑"""
        ri_gan = params.get('ri_gan', '')
        ri_zhi = params.get('ri_zhi', '')
        yue_jiang = params.get('yue_jiang', '')
        shi_chen = params.get('shi_chen', '')
        
        if not all([ri_gan, ri_zhi, yue_jiang, shi_chen]):
            self.send_json_response({
                'success': False,
                'error': '缺少必要参数：ri_gan, ri_zhi, yue_jiang, shi_chen'
            }, 400)
            return
        
        try:
            # 计算天地盘
            tiandi_pan = self.calculator.get_tiandi_pan(yue_jiang, shi_chen)
            
            # 起四课（不传 shi_chen）
            sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            
            # 发三传
            sanchuan_result = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            
            # 为三传添加天将、六亲、空亡信息
            if '三传' in sanchuan_result:
                san_chuan_list = sanchuan_result['三传']
                tian_jiang_list = []
                stem_list = []
                ganzhi_list = []
                liuqin_list = []
                kong_wang_list = []
                
                for chuan in san_chuan_list:
                    # 天将
                    tian_jiang = self.calculator.get_tian_jiang_for_chuan(chuan, ri_gan, tiandi_pan, shi_chen)
                    tian_jiang_list.append(tian_jiang)
                    
                    # 空亡判断（仅内部使用，不显示）
                    is_kw = is_kong_wang(chuan, ri_gan, ri_zhi)
                    
                    # 六亲
                    liuqin = self.liuqin_calc.get_liuqin(ri_gan, chuan)
                    liuqin_list.append(liuqin)
                    
                    # 遁干（空亡则天干留空不显示）
                    if is_kw:
                        # 空亡：天干留空
                        stem = ''
                        ganzhi = chuan  # 只显示地支
                    else:
                        # 不空亡：正常计算天干
                        stem = get_stem_for_branch(chuan, ri_gan, ri_zhi)
                        ganzhi = stem + chuan
                    
                    stem_list.append(stem)
                    ganzhi_list.append(ganzhi)
                    
                    # 空亡位置保留空字符占位（不显示空亡提示）
                    kong_wang_list.append('' if is_kw else '')
                
                sanchuan_result['三传天将'] = tian_jiang_list
                sanchuan_result['三传天干'] = stem_list
                sanchuan_result['三传干支'] = ganzhi_list
                sanchuan_result['三传六亲'] = liuqin_list
                sanchuan_result['三传空亡'] = kong_wang_list
            
            # 返回结果
            result = {
                'success': True,
                'data': {
                    'ri_gan': ri_gan,
                    'ri_zhi': ri_zhi,
                    'yue_jiang': yue_jiang,
                    'shi_chen': shi_chen,
                    'sike': sike,
                    'sanchuan': sanchuan_result
                }
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"错误：{error_msg}")
            self.send_json_response({
                'success': False,
                'error': str(e),
                'traceback': error_msg
            }, 500)


def run_server(port=5000):
    """运行服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ZongMenAPIHandler)
    print('=' * 60)
    print('宗门九课起课法 API 服务器已启动')
    print(f'访问地址：http://localhost:{port}/demo.html')
    print(f'API 文档：http://localhost:{port}/')
    print('按 Ctrl+C 停止服务器')
    print('=' * 60)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
