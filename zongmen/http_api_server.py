#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
宗门九课起课法 - HTTP API 服务器
为 HTML 系统提供后端 API 接口

使用方法:
    python http_api_server.py
    访问：http://localhost:5000
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi

# 添加路径 - 添加 src 目录以便能导入 utils 和 data 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'engine'))

# 在启动时导入模块
from sike_sanchuan_engine import SiKeSanChuanCalculator
from liuqin_engine import LiuQinCalculator
from gui_ren_engine import GuiRenCalculator


def get_xun_shou(ri_gan: str, ri_zhi: str) -> tuple:
    """
    计算日干支的旬首和旬中地支
    
    六甲旬：
    - 甲子旬：甲子、乙丑、丙寅、丁卯、戊辰、己巳、庚午、辛未、壬申、癸酉（戌亥空）
    - 甲戌旬：甲戌、乙亥、丙子、丁丑、戊寅、己卯、庚辰、辛巳、壬午、癸未（申酉空）
    - 甲申旬：甲申、乙酉、丙戌、丁亥、戊子、己丑、庚寅、辛卯、壬辰、癸巳（午未空）
    - 甲午旬：甲午、乙未、丙申、丁酉、戊戌、己亥、庚子、辛丑、壬寅、癸卯（辰巳空）
    - 甲辰旬：甲辰、乙巳、丙午、丁未、戊申、己酉、庚戌、辛亥、壬子、癸丑（寅卯空）
    - 甲寅旬：甲寅、乙卯、丙辰、丁巳、戊午、己未、庚申、辛酉、壬戌、癸亥（子丑空）
    
    :param ri_gan: 日干
    :param ri_zhi: 日支
    :return: (旬首天干，旬首地支，空亡地支列表)
    """
    # 天干地支顺序
    stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 计算日干支在 60 甲子中的序号
    # 使用公式：序号 = (天干索引 × 6 - 地支索引 × 5) % 60
    gan_index = stems.index(ri_gan)
    zhi_index = branches.index(ri_zhi)
    
    # 60 甲子序号计算
    ganzhi_index = (gan_index * 6 - zhi_index * 5) % 60
    if ganzhi_index < 0:
        ganzhi_index += 60
    
    # 旬首序号 = 60 甲子序号 // 10 × 10
    xun_shou_index = (ganzhi_index // 10) * 10
    
    # 旬首天干总是甲
    xun_shou_gan = '甲'
    
    # 旬首地支 = 旬首序号 % 12
    xun_shou_zhi = branches[xun_shou_index % 12]
    
    # 计算空亡（旬尾后两位）
    # 一旬 10 个干支，12 个地支，最后 2 个地支为空亡
    kong_wang_index1 = (xun_shou_index % 12 + 10) % 12
    kong_wang_index2 = (xun_shou_index % 12 + 11) % 12
    kong_wang = [branches[kong_wang_index1], branches[kong_wang_index2]]
    
    return xun_shou_gan, xun_shou_zhi, kong_wang


def get_stem_for_branch(branch: str, ri_gan: str, ri_zhi: str) -> str:
    """
    根据日干支计算地支的遁干（旬遁法）
    
    规则：
    1. 先确定日干支所属的旬
    2. 从旬首（甲 X）开始，按天干顺序顺排
    3. 找到目标地支对应的天干
    
    :param branch: 地支
    :param ri_gan: 日干
    :param ri_zhi: 日支
    :return: 遁干
    """
    stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 获取旬首
    xun_shou_gan, xun_shou_zhi, _ = get_xun_shou(ri_gan, ri_zhi)
    
    # 旬首地支的索引
    xun_index = branches.index(xun_shou_zhi)
    
    # 目标地支的索引
    branch_index = branches.index(branch)
    
    # 计算从旬首到目标地支的距离
    distance = (branch_index - xun_index) % 12
    
    # 如果距离 >= 10，说明该地支不在本旬内（是空亡），但还是要计算遁干
    # 遁干按天干顺序循环
    stem_index = distance % 10
    
    return stems[stem_index]


def is_kong_wang(branch: str, ri_gan: str, ri_zhi: str) -> bool:
    """
    判断地支是否为空亡
    
    :param branch: 地支
    :param ri_gan: 日干
    :param ri_zhi: 日支
    :return: 是否空亡
    """
    _, _, kong_wang = get_xun_shou(ri_gan, ri_zhi)
    return branch in kong_wang


class ZongMenAPIHandler(SimpleHTTPRequestHandler):
    """宗门九课 API 处理器"""
    
    def __init__(self, *args, **kwargs):
        self.calculator = SiKeSanChuanCalculator()
        self.liuqin_calculator = LiuQinCalculator()
        self.gui_ren_calculator = GuiRenCalculator()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        
        # 如果是 HTML 文件请求，返回文件内容
        if parsed_path.path.endswith('.html'):
            self.serve_html_file(parsed_path.path)
        elif parsed_path.path == '/api/qike':
            # 起课 API
            self.handle_qike_api(parsed_path)
        elif parsed_path.path == '/api/ke_li':
            # 查询课例 API
            self.handle_ke_li_api(parsed_path)
        elif parsed_path.path == '/api/stats':
            # 统计信息 API
            self.handle_stats_api()
        else:
            # 返回 API 文档
            self.send_api_docs()
    
    def serve_html_file(self, file_path):
        """提供 HTML 文件"""
        # 移除开头的斜杠
        if file_path.startswith('/'):
            file_path = file_path[1:]
        
        # 构建完整路径
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        
        if not os.path.exists(full_path):
            self.send_error(404, f"File not found: {file_path}")
            return
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/qike':
            # 起课 API (POST)
            self.handle_qike_api_post()
        else:
            self.send_error(404, "API not found")
    
    def send_json_response(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def handle_qike_api(self, parsed_path):
        """处理起课 API (GET)"""
        params = parse_qs(parsed_path.query)
        
        # 获取参数
        ri_gan = params.get('ri_gan', [''])[0]
        ri_zhi = params.get('ri_zhi', [''])[0]
        yue_jiang = params.get('yue_jiang', [''])[0]
        shi_chen = params.get('shi_chen', [''])[0]
        
        if not all([ri_gan, ri_zhi, yue_jiang, shi_chen]):
            self.send_json_response({
                'success': False,
                'error': '缺少必要参数：ri_gan, ri_zhi, yue_jiang, shi_chen'
            }, 400)
            return
        
        try:
            # 计算天地盘
            tiandi_pan = self.calculator.get_tiandi_pan(yue_jiang, shi_chen)
            
            # 起四课（包含天将）- 不传 shi_chen，使用默认值
            sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            
            # 发三传
            sanchuan_result = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            
            # 为三传添加天将信息
            # fa_sanchuan 返回格式：{'初传': str, '中传': str, '末传': str, ...}
            if '初传' in sanchuan_result and '中传' in sanchuan_result and '末传' in sanchuan_result:
                san_chuan_list = [
                    sanchuan_result['初传'],
                    sanchuan_result['中传'],
                    sanchuan_result['末传']
                ]
                tian_jiang_list = []
                stem_list = []  # 三传天干（遁干）
                ganzhi_list = []  # 三传干支
                liuqin_list = []  # 三传六亲
                kong_wang_list = []  # 空亡标记
                
                print(f"开始处理三传：{san_chuan_list}")
                
                for chuan in san_chuan_list:
                    try:
                        print(f"处理三传：{chuan}")
                        
                        # 天将 - 使用预导入的计算器
                        try:
                            # 获取天将盘
                            tian_jiang_map = self.gui_ren_calculator.arrange_gui_ren_pan(
                                ri_gan, 
                                {'天地对应': tiandi_pan}, 
                                shi_chen
                            )
                            tian_jiang = tian_jiang_map.get('天将映射', {}).get(chuan, '')
                            print(f"  天将：{tian_jiang}")
                        except Exception as e:
                            print(f"获取天将失败：{e}")
                            import traceback
                            traceback.print_exc()
                            tian_jiang = ''
                        tian_jiang_list.append(tian_jiang)
                        
                        # 空亡判断（仅内部使用，不显示）
                        is_kw = is_kong_wang(chuan, ri_gan, ri_zhi)
                        
                        # 六亲
                        try:
                            liuqin = self.liuqin_calculator.get_liuqin(ri_gan, chuan)
                            print(f"  六亲：{liuqin}")
                        except Exception as e:
                            print(f"获取六亲失败：{e}")
                            liuqin = ''
                        liuqin_list.append(liuqin)
                        
                        # 遁干（空亡则天干留空不显示）
                        if is_kw:
                            # 空亡：天干留空
                            stem = ''
                            ganzhi = chuan  # 只显示地支
                        else:
                            # 不空亡：正常计算天干
                            try:
                                stem = get_stem_for_branch(chuan, ri_gan, ri_zhi)
                            except Exception as e:
                                print(f"获取遁干失败：{e}")
                                stem = ''
                            ganzhi = stem + chuan
                        
                        stem_list.append(stem)
                        ganzhi_list.append(ganzhi)
                        
                        # 空亡位置保留空字符占位（不显示空亡提示）
                        kong_wang_list.append('' if is_kw else '')
                        
                        print(f"  结果：六亲={liuqin}, 干支={ganzhi}, 天将={tian_jiang}, 空亡={kong_wang_list[-1]}")
                        
                    except Exception as e:
                        print(f"处理三传 {chuan} 时出错：{e}")
                        import traceback
                        traceback.print_exc()
                        # 出错时使用默认值
                        tian_jiang_list.append('')
                        stem_list.append('')
                        ganzhi_list.append(chuan)
                        liuqin_list.append('')
                        kong_wang_list.append('')
                
                # 添加新字段到返回结果
                sanchuan_result['三传'] = san_chuan_list
                sanchuan_result['三传天将'] = tian_jiang_list
                sanchuan_result['三传天干'] = stem_list
                sanchuan_result['三传干支'] = ganzhi_list
                sanchuan_result['三传六亲'] = liuqin_list
                sanchuan_result['三传空亡'] = kong_wang_list
                
                print(f"三传处理完成：{sanchuan_result}")
            
            # 返回结果
            result = {
                'success': True,
                'data': {
                    'ri_gan': ri_gan,
                    'ri_zhi': ri_zhi,
                    'yue_jiang': yue_jiang,
                    'shi_chen': shi_chen,
                    'tiandi_pan': tiandi_pan,
                    'sike': sike,
                    'sanchuan': sanchuan_result
                }
            }
            
            self.send_json_response(result)
        
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    def handle_qike_api_post(self):
        """处理起课 API (POST)"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data)
            
            ri_gan = data.get('ri_gan', '')
            ri_zhi = data.get('ri_zhi', '')
            yue_jiang = data.get('yue_jiang', '')
            shi_chen = data.get('shi_chen', '')
            
            if not all([ri_gan, ri_zhi, yue_jiang, shi_chen]):
                self.send_json_response({
                    'success': False,
                    'error': '缺少必要参数：ri_gan, ri_zhi, yue_jiang, shi_chen'
                }, 400)
                return
            
            # 计算
            tiandi_pan = self.calculator.get_tiandi_pan(yue_jiang, shi_chen)
            sike = self.calculator.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            sanchuan_result = self.calculator.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            
            result = {
                'success': True,
                'data': {
                    'ri_gan': ri_gan,
                    'ri_zhi': ri_zhi,
                    'yue_jiang': yue_jiang,
                    'shi_chen': shi_chen,
                    'tiandi_pan': tiandi_pan,
                    'sike': sike,
                    'sanchuan': sanchuan_result
                }
            }
            
            self.send_json_response(result)
        
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    def handle_ke_li_api(self, parsed_path):
        """处理课例查询 API"""
        params = parse_qs(parsed_path.query)
        ri_gan_zhi = params.get('ri_gan_zhi', [''])[0]
        yue = params.get('yue', [''])[0]
        shi = params.get('shi', [''])[0]
        
        # 加载数据
        data_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li_jiu_zong_men.json')
        if not os.path.exists(data_file):
            self.send_json_response({'success': False, 'error': '数据文件不存在'}, 404)
            return
        
        with open(data_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        
        ke_li = full_data.get('ke_li', {})
        
        # 搜索
        results = []
        for key, value in ke_li.items():
            if ri_gan_zhi and not key.startswith(ri_gan_zhi):
                continue
            if yue and f"_{yue}_" not in key:
                continue
            if shi and not key.endswith(f"_{shi}"):
                continue
            
            results.append({
                'key': key,
                'data': value
            })
            
            if len(results) >= 100:  # 限制返回数量
                break
        
        self.send_json_response({
            'success': True,
            'count': len(results),
            'results': results
        })
    
    def handle_stats_api(self):
        """处理统计信息 API"""
        data_file = os.path.join(os.path.dirname(__file__), 'data', '720_ke_li_jiu_zong_men.json')
        if not os.path.exists(data_file):
            self.send_json_response({'success': False, 'error': '数据文件不存在'}, 404)
            return
        
        with open(data_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        
        metadata = full_data.get('metadata', {})
        
        self.send_json_response({
            'success': True,
            'data': metadata
        })
    
    def send_api_docs(self):
        """发送 API 文档"""
        docs = {
            'name': '宗门九课起课法 API',
            'version': '1.0.0',
            'endpoints': {
                'GET /api/qike': {
                    'description': '起课（GET 方式）',
                    'parameters': {
                        'ri_gan': '日干（甲、乙、丙、丁...）',
                        'ri_zhi': '日支（子、丑、寅、卯...）',
                        'yue_jiang': '月将（子、丑、寅、卯...）',
                        'shi_chen': '时辰（子、丑、寅、卯...）'
                    },
                    'example': '/api/qike?ri_gan=甲&ri_zhi=子&yue_jiang=丑&shi_chen=子'
                },
                'POST /api/qike': {
                    'description': '起课（POST 方式）',
                    'content_type': 'application/json',
                    'body': {
                        'ri_gan': '甲',
                        'ri_zhi': '子',
                        'yue_jiang': '丑',
                        'shi_chen': '子'
                    }
                },
                'GET /api/ke_li': {
                    'description': '查询课例',
                    'parameters': {
                        'ri_gan_zhi': '日干支（可选）',
                        'yue': '月建（可选）',
                        'shi': '时辰（可选）'
                    },
                    'example': '/api/ke_li?ri_gan_zhi=甲子&yue=子&shi=子'
                },
                'GET /api/stats': {
                    'description': '获取统计信息'
                }
            }
        }
        
        self.send_json_response(docs)
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server(port=5000):
    """运行 API 服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ZongMenAPIHandler)
    print(f"=" * 60)
    print(f"宗门九课起课法 API 服务器已启动")
    print(f"访问地址：http://localhost:{port}")
    print(f"API 文档：http://localhost:{port}/")
    print(f"按 Ctrl+C 停止服务器")
    print(f"=" * 60)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
