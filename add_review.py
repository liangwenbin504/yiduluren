with open('stock_dashboard.html','r',encoding='utf-8') as f:
    htm = f.read()

if 'function runLiurenReview' in htm:
    print('ALREADY EXISTS')
else:
    func = '''\nfunction runLiurenReview(etfName) {
  var panel = document.getElementById('liurenReviewPanel');
  if(!panel) {
    panel = document.createElement('div');
    panel.id = 'liurenReviewPanel';
    panel.style.cssText = 'position:fixed;top:60px;right:10px;width:420px;max-height:85vh;overflow-y:auto;background:#fff;border-radius:14px;padding:20px;z-index:9999;box-shadow:0 8px 40px rgba(0,0,0,.3);font-size:13px;line-height:1.6;';
    var c = document.createElement('div'); c.textContent = '\\u00d7'; c.style.cssText = 'position:absolute;top:10px;right:14px;cursor:pointer;font-size:24px;color:#999;';
    c.onclick = function(){ panel.remove(); }; panel.appendChild(c);
    document.body.appendChild(panel);
  }
  panel.innerHTML = '<div style=text-align:center;padding:40px;color:#999;>\\u{1f52e} '+etfName+' 起课中...</div>';
  fetch(API+'/api/liuren_20d?force=1').then(function(r){return r.json();}).then(function(d){
    if(!d.data) { panel.innerHTML='<div style=text-align:center;padding:40px;color:#e74c3c;>失败</div>'; return; }
    var dd=d.data, bi=dd.basic_info||{}, p=dd.prediction||{}, tc=p.trend.indexOf('涨')>=0?'#27ae60':'#e74c3c';
    fetch(API+'/api/liuren_review/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({etf:etfName,data:dd})}).catch(function(){});
    var h='<div style=font-size:17px;font-weight:700;margin-bottom:14px;color:#333;>' + etfName + ' 六壬复盘</div>';
    h+='<div style=background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-radius:10px;padding:14px;margin-bottom:12px;>';
    h+='<div><b>四柱:</b> '+(bi.ri_gan_zhi||'?')+'日 '+(bi.shichen||'?')+'时</div>';
    h+='<div><b>月将:</b> '+(bi.yuejiang||'?')+' ('+(bi.yuejiang_name||'')+')</div></div>';
    h+='<div style=margin-bottom:6px;><b>课体:</b> '+(dd.keti||'--')+'</div>';
    h+='<div style=margin-bottom:6px;><b>三传:</b> '+(dd.san_chuan||[]).join(' / ')+'</div>';
    h+='<div style=text-align:center;margin:16px 0;><div style=font-size:28px;font-weight:900;color:'+tc+';>'+p.trend+'</div>';
    h+='<div>评分: '+p.score+' | 置信度: '+p.confidence+'%</div></div>';
    h+='<div style=font-size:11px;color:#666;border-top:1px solid #eee;padding-top:8px;>';
    (p.reasons||[]).slice(0,5).forEach(function(r){ h+='<div> - '+r+'</div>'; });
    h+='</div>';
    panel.innerHTML = h;
  }).catch(function(){ panel.innerHTML='<div style=text-align:center;padding:40px;color:#e74c3c;>请求失败</div>'; });
}
'''
    htm = htm.replace('    </script>', func + '\n    </script>')
    with open('stock_dashboard.html','w',encoding='utf-8') as f:
        f.write(htm)
    print('ADDED')

# 按钮
old_btn = '<td><strong>${etf.score}</strong></td>'
if old_btn in htm and '六壬复盘' not in htm:
    new_btn = '<td><strong>${etf.score}</strong></td>\n        <td>${etf.confidence < 50 ? \'<button onclick=\"runLiurenReview(\\'+etf.name+\'\\')\" style=\"background:#8b5cf6;color:#fff;border:none;padding:2px 8px;border-radius:3px;cursor:pointer;font-size:11px;\">六壬复盘</button>\' : \'\'}</td>'
    htm = htm.replace(old_btn, new_btn)
    with open('stock_dashboard.html','w',encoding='utf-8') as f:
        f.write(htm)
    print('BUTTON ADDED')

assert '<!DOCTYPE html>' in htm
print('OK')
