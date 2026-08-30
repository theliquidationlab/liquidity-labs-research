const $=id=>document.getElementById(id); let lastGeneratedMs=0;
const num=n=>new Intl.NumberFormat().format(Number(n||0));
const pct=v=>v===null||v===undefined?'PENDING':`${Number(v).toFixed(2)}%`;
function setText(id,v){$(id).textContent=v}
function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function metricClass(el,v,target=98){el.classList.remove('good','warn','bad');if(v===null||v===undefined)return;if(v>=target)el.classList.add('good');else if(v>=80)el.classList.add('warn');else el.classList.add('bad')}
function render(d){
  const h=d.system||{}; setText('healthLabel',h.label||'UNKNOWN');setText('activeStage',h.active_stage||'No active stage');
  $('healthDot').style.background=h.working?'#56dea7':'#ffb84d';$('healthDot').style.boxShadow=`0 0 0 5px ${h.working?'#56dea722':'#ffb84d22'}`;
  const p=d.progress||{};setText('overallPct',`${Number(p.overall||0).toFixed(1)}%`);$('overallBar').style.width=`${Math.max(0,Math.min(100,p.overall||0))}%`;
  setText('dataPct',`${Number(p.data_build||0).toFixed(1)}%`);setText('validationPct',`${Number(p.validation||0).toFixed(1)}%`);
  const when=d.generated_utc?new Date(d.generated_utc):null;lastGeneratedMs=when?when.getTime():0;setText('updatedAt',when?when.toLocaleString():'--');
  const m=d.metrics||{};setText('mt5Wr',pct(m.mt5_win_rate));setText('mt5Label',m.mt5_label||'--');metricClass($('mt5Wr'),m.mt5_win_rate);
  setText('binanceWr',pct(m.binance_win_rate));setText('binanceLabel',m.binance_label||'--');metricClass($('binanceWr'),m.binance_win_rate);
  setText('combinedWr',pct(m.combined_win_rate));setText('combinedLabel',m.combined_label||'--');metricClass($('combinedWr'),m.combined_win_rate);
  setText('tradesDay',Number(m.qualifying_trades_per_day||0).toFixed(2));setText('tradeTarget',`Target: ≥${m.trade_target_per_day||100}/day at ≥${m.target_win_rate||98}% WR`);
  const c=d.counts||{};setText('tickCount',num(c.mt5_ticks));setText('stateDays',`${c.state_days_complete||0}/${c.state_days_total||365}`);setText('featureCount',num(c.mt5_features));setText('ruleCount',num(c.prior_exact_bin_rules));
  const stages=d.stages||[];const done=stages.filter(s=>s.state==='complete').length;setText('stageCount',`${done}/${stages.length} complete`);
  $('stageList').innerHTML=stages.map(s=>{const icon=s.state==='complete'?'✓':s.state==='working'?'↻':'•';const finding=s.finding?`<p class="finding">${escapeHtml(s.finding)}</p>`:'';return `<article class="stage ${escapeHtml(s.state)}"><div class="stage-icon">${icon}</div><div><h3>${escapeHtml(s.name)}</h3><p>${escapeHtml(s.detail)}</p>${finding}</div><div class="state">${escapeHtml(s.state)}</div></article>`}).join('');
  $('notes').innerHTML=(d.notes||[]).map(x=>`<li>${escapeHtml(x)}</li>`).join('');
}
async function refresh(){try{const r=await fetch(`https://raw.githubusercontent.com/theliquidationlab/liquidity-labs-research/main/data/status.json?t=${Date.now()}`,{cache:'no-store'});if(!r.ok)throw new Error(`HTTP ${r.status}`);render(await r.json())}catch(e){setText('healthLabel','DATA OFFLINE');setText('activeStage','Dashboard could not load fresh status');$('healthDot').style.background='#ff7373'}}
function staleCheck(){if(lastGeneratedMs&&Date.now()-lastGeneratedMs>20*60*1000){setText('healthLabel','STATUS STALE');setText('activeStage','VPS feed has not refreshed recently');$('healthDot').style.background='#ff7373'}}
refresh();setInterval(refresh,60000);setInterval(staleCheck,30000);
