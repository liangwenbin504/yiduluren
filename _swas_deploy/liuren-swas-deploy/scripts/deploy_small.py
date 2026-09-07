#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【2026-09-07】小 diff 包专用部署：CSZ=3000（单命令 <6.3KB 安全线）避免 SWAS 命令损坏。
仅用于 diff 包 ≤ ~30KB 的场景（如单文件引擎修复）。复用 deploy.py 传输/校验/安装流程。"""
import sys, os, base64, time, uuid, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deploy as _dep

def main():
    tar = sys.argv[1] if len(sys.argv) > 1 else r'E:\仪度六壬择日\yiduluren\liuren-deploy.tar.gz'
    # 先做 diff（复用 deploy 的 build_diff_tarball）
    diff_tar, changed = _dep.build_diff_tarball(tar)
    if diff_tar is None:
        print('[diff] 服务器 /opt/liuren 与本地包完全一致，无需部署。')
        return
    print('[diff] 变更文件数:', len(changed))
    for c in changed:
        print('   -', c)

    data = open(diff_tar, 'rb').read()
    b64 = base64.b64encode(data).decode()
    EXP = len(b64)
    B64_SHA = hashlib.sha256(b64.encode()).hexdigest()
    NONCE = uuid.uuid4().hex[:8]
    CSZ = 3000  # 关键：小块，命令 <6.3KB 安全线
    chunks = [b64[i:i + CSZ] for i in range(0, len(b64), CSZ)]
    N = len(chunks)
    print(f'[info] {N} 块(CSZ={CSZ}), 期望 {EXP} 字节, nonce={NONCE}')

    _dep.cmd('rm -f /tmp/lp_w*.b64 /tmp/lp.b64', 'clean' + NONCE, 30)
    print('[1] 分文件明文传输 ...')
    ok = 0
    for i, ch in enumerate(chunks):
        name = f'w{NONCE}{i:03d}'  # 命令名带 nonce，避开 SWAS 命令幂等去重
        c = f"printf '%s' '{ch}' > /tmp/lp_w{i:03d}.b64"
        r = _dep.cmd(c, name, 60)
        if 'InvokeId' in r:
            ok += 1
        else:
            print('  !块%d: %s' % (i, str(r)[:150]))
        time.sleep(0.08)
    print(f'  传输 {ok}/{N}')
    if ok < N:
        sys.exit('❌ 传输阶段存在失败块，放弃')

    print('[2] 校验 ...')
    verify = f'''
rm -f /tmp/lp.b64
for i in $(seq -f '%03g' 0 {N-1}); do cat /tmp/lp_w$i.b64; done > /tmp/lp.b64
sz=$(wc -c < /tmp/lp.b64)
sha=$(sha256sum < /tmp/lp.b64 | cut -d' ' -f1)
echo "size=$sz sha=$sha exp_size={EXP} exp_sha={B64_SHA}"
'''
    passed = False
    for attempt in range(4):
        st, dec = _dep.getout(_dep.cmd(verify, 'v' + NONCE + str(attempt), 120).get('InvokeId'), 120)
        print(dec.strip()[:400])
        if f'size={EXP}' in dec and B64_SHA in dec:
            passed = True
            break
        time.sleep(2)
    if not passed:
        sys.exit('❌ 校验未通过，放弃安装')

    print('[3] 安装 ...')
    install = f'''
base64 -d /tmp/lp.b64 > /root/liuren-deploy.tar.gz && echo "解码 OK $(ls -lh /root/liuren-deploy.tar.gz | awk '{{print $5}}')" || {{ echo "解码失败"; exit 7; }}
mkdir -p /opt/liuren
tar -xzf /root/liuren-deploy.tar.gz -C /opt/liuren && echo "解压 OK" || {{ echo "解压失败"; exit 8; }}
cd /opt/liuren; ls -lh douhou_analyzer.py engine/douhou_analyzer.py 2>/dev/null || true
bash install_on_server.sh
echo "=== INSTALL rc=$? ==="
sleep 3
echo "--- 本地 5555 自检 ---"; curl -s http://127.0.0.1:5555/ | head -c 200; echo
echo "--- systemd liuren ---"; systemctl is-active liuren
rm -f /tmp/lp_w*.b64 /tmp/lp.b64 /root/liuren-deploy.tar.gz
echo "=== DEPLOY_END ==="
'''
    st, out = _dep.getout(_dep.cmd(install, 'inst' + NONCE, 900).get('InvokeId'), 500)
    print('[install]', st)
    print(out.strip()[-1800:])
    os.remove(diff_tar)

if __name__ == '__main__':
    main()