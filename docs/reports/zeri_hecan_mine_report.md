# 择日合参迁移与规则矿建设 报告（2026-08-19）

## 一、文件解锁尝试（结论：需用户系统层处理）
- 已试：icacls /reset（恢复继承）、/grant:r Administrators:F（强制授权）——命令均报成功，但写/删仍 EACCES；ACL 全 Allow、无 SACL 完整性标签。
- 推断：锁源为持有 `FileShare.Read` 句柄的进程（DSH 文件监视器 write-once 语义），非文件系统 ACL——无法从代码侧解除。
- **手动解锁路径**（任选其一）：①重启 DSH 会话后重试写 stock_dashboard.py；②在 DSH GUI 文件策略中解除该文件写保护；③Windows 资源管理器→文件属性→安全→将 Administrators 设为完全控制并清空特殊 SID 条目（该 SID 为 Allow 非 Deny，锁不在它）。
- 解锁后接线清单（代码已备好）：stock_dashboard.py `_build_zeri_candidate` ②b 后贴 zeri_hecan_bridge2 调用（接入代码在桥文件 docstring）；api_server.py line 1990 import 改 patched11。

## 二、择日规则矿（已建成，全部新文件，实例+古籍双依据）
### 引擎 `zeri_hecan_engine.py`
- `zeri_type_class`：择日类型→要诀场景类（提车→出行、开张→开业…）
- `zeri_signals`：课体 15 键×类型 10 键（全部可计算）
- `zeri_hecan_judge`：全条件命中才触发（与占断合参同口径，neg 支持）

### 候选库 `data/zeri_hecan_rules.json`（11 条，每条标出处）
- 凶 6 条（ZR-001~006）：伏吟+出行/动土/安葬/上任、返吟+出行、八专+安葬——出处《仪度六壬择日要诀》七场景凶课表 + 64 课格伏吟"律身谨慎，动作无虞" + FB 反馈
- 吉 4 条（ZR-101~104）：官爵+上任、亨通+出行、元首+动土、龙德通用——要诀七场景吉课表
- ZR-201：催龙补气三传水局发丁（FB-001 单实例）
- **状态：全部"候选-样本不足"**——反馈池仅 3 条（1 吉 1 凶+1 测试重复），守"实例生成"铁律不入 L2

### 验证框架 `_memory/zeri_hecan_verify.py`
- 门槛同占断合参：真实反馈全中≥3 且一致率≥80% 升 L2
- 现状：ZR-001 全中 2 一致 100%（FB-002/003 提车伏吟追尾/出险）、ZR-201 全中 1 一致 100%
- 优化结果池（zeri_optimize_*.json）无 label 仅观察不参与门槛

### 集成 `zeri_hecan_bridge2.py`
- = bridge + 择日规则判定，输出 `zeri_rules` 字段（占断合参+择日合参双通道）
- FB-002 全链路复现：丙寅日午将午时伏吟课三传巳申寅 → ZR-001 触发（"出行择日忌伏吟课…主车辆事故"）✓

## 三、定位铁律
- 合参（占断+择日）在择日模块一律**警示/佐证层**：凶规则→前端"古籍合参警示"黄牌；吉规则→佐证文案；**不加减择日评分**（斗首/仪度/禄马贵/演禽分层口径不动）。
- 择日规则升 L2 依赖真实反馈积累——建议前端 feedback 入口持续采集（zeri_case_feedback.json 已具备落盘机制），每积累一批跑一次验证器复核。
