"""
大六壬详细排盘显示工具
"""

def format_daliuren_detail(result: dict) -> str:
    """
    格式化大六壬详细排盘结果
    """
    output = []
    output.append("═" * 60)
    output.append("大六壬详细排盘")
    output.append("═" * 60)
    
    # 基本信息
    output.append(f"\n【基本信息】")
    output.append(f"  月将：{result['月将']}")
    output.append(f"  占时：{result['占时']}")
    output.append(f"  日柱：{result['日柱']}")
    
    # 天地盘（只显示天盘）
    output.append(f"\n【天地盘】")
    tian_pan = result['天地盘']['天盘']
    
    # 只显示天盘，对齐显示
    output.append(f"  天盘：子    丑    寅    卯    辰    巳    午    未    申    酉    戌    亥")
    tian_line = "        "
    for tianzhi in tian_pan:
        tian_line += f"{tianzhi}    "
    output.append(tian_line)
    
    # 四课
    output.append(f"\n\n【四课】")
    for ke in result['四课']:
        output.append(f"  {ke['name']}: {ke['top']}（上） {ke['bottom']}（下）")
    
    # 四课表格形式
    output.append(f"\n  四课图示：")
    output.append(f"  ┌──────┬──────┬──────┬──────┐")
    output.append(f"  │ 第四课 │ 第三课 │ 第二课 │ 第一课 │")
    output.append(f"  ├──────┼──────┼──────┼──────┤")
    
    # 上神
    shang_list = [ke['top'] for ke in result['四课']]
    output.append(f"  │  {shang_list[3]:^2}  │  {shang_list[2]:^2}  │  {shang_list[1]:^2}  │  {shang_list[0]:^2}  │  ←上神")
    output.append(f"  ├──────┼──────┼──────┼──────┤")
    
    # 下神
    xia_list = [ke['bottom'] for ke in result['四课']]
    output.append(f"  │  {xia_list[3]:^2}  │  {xia_list[2]:^2}  │  {xia_list[1]:^2}  │  {xia_list[0]:^2}  │  ←下神")
    output.append(f"  └──────┴──────┴──────┴──────┘")
    
    # 天将
    output.append(f"\n【天将】")
    for tj in result['天将']:
        output.append(f"  {tj['天将']:4} - {tj['地支']}")
    
    # 天将表格
    output.append(f"\n  天将排布：")
    output.append(f"  ┌────────────────────────────────┐")
    for i in range(0, 12, 3):
        tj1 = result['天将'][i]
        tj2 = result['天将'][i+1] if i+1 < 12 else None
        tj3 = result['天将'][i+2] if i+2 < 12 else None
        line = f"  │"
        line += f" {tj1['天将']}{tj1['地支']:^2} │"
        if tj2:
            line += f" {tj2['天将']}{tj2['地支']:^2} │"
        if tj3:
            line += f" {tj3['天将']}{tj3['地支']:^2} │"
        output.append(line)
    output.append(f"  └────────────────────────────────┘")
    
    # 三传
    output.append(f"\n【三传】")
    san_chuan = result['三传']
    output.append(f"  课体：{san_chuan['课体']}")
    output.append(f"  起法：{san_chuan['起法']}")
    output.append(f"  初传：{san_chuan['三传'][0] if san_chuan['三传'] else ''}")
    output.append(f"  中传：{san_chuan['三传'][1] if len(san_chuan['三传']) > 1 else ''}")
    output.append(f"  末传：{san_chuan['三传'][2] if len(san_chuan['三传']) > 2 else ''}")
    
    # 课格
    ke_ge = result.get('课格', {})
    if ke_ge:
        output.append(f"\n【课格】")
        output.append(f"  名称：{ke_ge.get('课格名称', '')}")
        output.append(f"  说明：{ke_ge.get('课格说明', '')}")
        output.append(f"  吉凶：{ke_ge.get('吉凶', '')}")
    
    # 禄马贵
    output.append(f"\n【禄马贵】")
    lu_ma_gui = result['禄马贵']
    output.append(f"  禄神：{lu_ma_gui['禄']}")
    output.append(f"  驿马：{lu_ma_gui['驿马']}")
    output.append(f"  贵人：{', '.join(lu_ma_gui['贵人'])}")
    
    output.append("\n" + "═" * 60)
    
    return "\n".join(output)


# 测试
if __name__ == '__main__':
    from engine.daliuren_engine_pro import DaLiuRenEnginePro
    
    engine = DaLiuRenEnginePro()
    result = engine.full_pai_pan(1, '午', '甲', '子')
    
    print(format_daliuren_detail(result))
