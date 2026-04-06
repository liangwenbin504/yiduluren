# 新的六壬评分逻辑
# 规则：
# 1. 日柱禄马贵人必须有一项到山或到向才算合格（硬性条件）
# 2. 年月日时四柱禄马贵人同时到山到向为满分100分
# 3. 差一项依次递减

# 检查日柱是否合格（必须条件）
ri_qualified = (ri_result['shan_count'] > 0 or ri_result['xiang_count'] > 0)

if not ri_qualified:
    # 日柱不合格，只能算平课
    daliuren_score = 50
    qualified_status = '平课（日柱禄马贵人未到山到向）'
else:
    # 日柱合格，计算四柱合格数
    nian_qualified = (nian_result['shan_count'] > 0 or nian_result['xiang_count'] > 0)
    yue_qualified = (yue_result['shan_count'] > 0 or yue_result['xiang_count'] > 0)
    
    # 四柱合格数（年、月、日）
    qualified_count = sum([nian_qualified, yue_qualified, ri_qualified])
    
    # 评分规则：
    # 三柱全合格（年月日）= 100分
    # 两柱合格 = 75分
    # 仅日柱合格 = 60分
    if qualified_count >= 3:
        daliuren_score = 100
        qualified_status = '上吉课（年月日禄马贵人皆到山到向）'
    elif qualified_count >= 2:
        daliuren_score = 75
        qualified_status = '中吉课（两柱禄马贵人到山到向）'
    else:
        daliuren_score = 60
        qualified_status = '吉课（仅日柱禄马贵人到山到向）'

# 课体等级调整
if ke_level in ['大凶', '凶']:
    daliuren_score = max(30, daliuren_score - 20)
    qualified_status += ' [课体凶，扣20分]'
elif ke_level == '下吉':
    daliuren_score = max(40, daliuren_score - 10)
    qualified_status += ' [课体下吉，扣10分]'
elif ke_level == '上吉':
    daliuren_score = min(100, daliuren_score + 5)
    qualified_status += ' [课体上吉，加5分]'

daliuren_score = min(100, max(30, daliuren_score))
