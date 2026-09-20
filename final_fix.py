import codecs, re

with codecs.open('stock_dashboard.html','r','utf-8') as f:
    htm = f.read()

func = '''
function runLiurenReview(etfName) {
  var p=document.getElementById('liurenReviewPanel');
  if(!p){
    p=document.createElement('div');p.id='liurenReviewPanel';
    p.style.cssText='position:fixed;top:60px;right:10px;width:420px;max-height:85vh;overflow-y:auto;background:#fff;border-radius:14px;padding:20px;z-index:9999;box-shadow:0 8px 40px rgba(0,0,0,.3);font-size:13px;line-height:1.6;';
    var c=document.createElement('div');c.textContent='x';c.style.cssText='position:absolute;top:10px;right:14px;cursor:pointer;font-size:24px;color:#999;';
    c.onclick=function(){p.remove();};p.appendChild(c);document.body.appendChild(p);
  }
  p.innerHTML='<div style=text-align:center;padding:40px;color:#999;>起课中...</div>';
  fetch(API+'/api/liuren_20d?force=1').then(function(r){return r.json();}).then(function(d){
    if(!d.data){p.innerHTML='<div style=text-align:center;padding:40px;color:#e74c3c;>起课失败</div>';return;}
    var dd=d.data,bi=dd.basic_info||{},pr=dd.prediction||{},tc=pr.trend.indexOf('涨')>=0?'#27ae60':'#e74c3c';
    var h=etfName+'<br>四柱: '+(bi.ri_gan_zhi||'?')+' '+(bi.shichen||'?')+'时 月将: '+(bi.yuejiang||'?')+'<br>';
    h+='课体: '+(dd.keti||'--')+' 三传: '+(dd.san_chuan||[]).join('/')+'<br><br>';
    h+='<span style=font-size:28px;font-weight:900;color:'+tc+';>'+pr.trend+'</span><br>';
    h+='评分:'+pr.score+' 置信度:'+pr.confidence+'%<br><br>';
    h+='<span style=font-size:11px;color:#666;>'+(pr.reasons||[]).slice(0,5).join('<br>')+'</span>';
    p.innerHTML=h;
  }).catch(function(){p.innerHTML='<div style=text-align:center;padding:40px;color:#e74c3c;>失败</div>';});
}
function append_btn(name){return '<button onclick="runLiurenReview(\\''+name+'\\')" style="background:#8b5cf6;color:#fff;border:none;padding:2px 8px;border-radius:3px;cursor:pointer;font-size:11px;">复盘</button>';}
'''

# 在 </body> 前插入
htm = htm.replace('</body>', '<script>' + func + '</script>\n</body>')

# 加置信度表头
htm = htm.replace(
    '<th>RSI</th><th>均线趋势</th><th>推荐仓位</th><th>综合评分</th>',
    '<th>RSI</th><th>均线趋势</th><th>置信度</th><th>推荐仓位</th><th>综合评分</th>'
)

# 加置信度列 + 六壬复盘按钮
htm = htm.replace(
    '<td>${etf.rsi}</td>\n        <td>${etf.ma_trend||\'--\'}</td>\n        <td>${etf.position}%</td>\n        <td><strong>${etf.score}</strong></td>',
    '<td>${etf.rsi}</td>\n        <td>${etf.ma_trend||\'--\'}</td>\n        <td style="color:${etf.confidence>=70?\'#27ae60\':(etf.confidence>=50?\'#f39c12\':\'#e74c3c\')};font-weight:700;">${etf.confidence||0}%</td>\n        <td>${etf.position}%</td>\n        <td><strong>${etf.score}</strong></td>\n        <td>${etf.confidence < 50 ? append_btn(etf.name) : \'\'}</td>'
)

with codecs.open('stock_dashboard.html','w','utf-8') as f:
    f.write(htm)

assert '<!DOCTYPE html>' in htm
assert 'runLiurenReview' in htm
print('ALL OK')
