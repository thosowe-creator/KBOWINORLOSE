const $ = (q) => document.querySelector(q);
const $$ = (q) => [...document.querySelectorAll(q)];
const logo = {"LG":"🧢","한화":"🦅","롯데":"🌊","KIA":"🐯","SSG":"🚀","KT":"🧙","삼성":"🦁","NC":"🦖","두산":"🐻","키움":"🦸"};
let state = null;

async function loadData(){
  const res = await fetch(`data/current.json?ts=${Date.now()}`);
  state = await res.json();
  renderHeader(); renderMatches(); renderTeams(); renderSchedule(); renderVerify();
}
function renderHeader(){
  $('#subtitle').textContent = state.summary || 'KBO 자동 전력분석 대시보드';
  $('#todayLabel').textContent = state.date_label || state.date;
  $('#modeLabel').textContent = state.mode_label || '사전 분석';
  $('#updatedAt').textContent = `업데이트 ${state.updated_at_kst}`;
  $('#lineupStatus').textContent = state.lineup_status_label || '라인업 예상';
}
function renderMatches(){
  const root = $('#matchGrid'); root.innerHTML = '';
  state.games.forEach((g, idx)=>{
    const awayW = Math.max(8, Math.min(92, g.away.win_probability));
    const homeW = Math.max(8, Math.min(92, g.home.win_probability));
    const el = document.createElement('article'); el.className='matchCard';
    el.innerHTML = `<p class="matchMeta"><span>${g.time} · ${g.stadium}</span><span>${g.lineup_status}</span></p>
      <div class="probBox">
        <div class="side away" style="width:${awayW}%"><div class="bar" style="width:100%"></div><span class="logo">${logo[g.away.team]||'⚾'}</span><div class="teamMini"><div class="teamName">${g.away.team}</div><div class="pct">${g.away.win_probability}%</div></div></div>
        <div class="side home" style="width:${homeW}%"><div class="bar" style="width:100%"></div><div class="teamMini"><div class="teamName">${g.home.team}</div><div class="pct">${g.home.win_probability}%</div></div><span class="logo">${logo[g.home.team]||'⚾'}</span></div>
      </div>
      <div class="cardBottom"><div class="metric"><small>예상 기대득점</small><b>${g.away.team} ${g.away.expected_runs} - ${g.home.expected_runs} ${g.home.team}</b></div><div class="metric"><small>핵심 변수</small><b>${g.key_factor}</b></div></div>`;
    el.onclick=()=>renderReport(g); root.appendChild(el);
    if(idx===0) renderReport(g);
  });
}
function renderReport(g){
  $('#selectedReport').classList.remove('empty');
  $('#selectedReport').innerHTML = `<div class="reportTitle"><div><h2>${g.away.team} vs ${g.home.team}</h2><p>${g.time} · ${g.stadium}</p></div><span class="pill">${g.away.win_probability}% : ${g.home.win_probability}%</span></div>
    <p>${g.report}</p>
    <div class="reportGrid">
      <div class="metric"><small>선발</small><b>${g.away.starter} vs ${g.home.starter}</b></div>
      <div class="metric"><small>예측 신뢰도</small><b>${g.confidence}</b></div>
      <div class="metric"><small>라인업</small><b>${g.lineup_status}</b></div>
      <div class="metric"><small>검증</small><b>${g.validation_passes}회 통과</b></div>
    </div>
    <h3>체크 포인트</h3><ul class="list">${g.notes.map(n=>`<li>${n}</li>`).join('')}</ul>`;
}
function renderTeams(){
  const root=$('#teamGrid'); root.innerHTML='';
  state.teams.forEach(t=>{
    const el=document.createElement('article'); el.className='teamCard';
    el.innerHTML=`<div class="teamTop"><h3>${logo[t.team]||'⚾'} ${t.team}</h3><span class="rank">${t.rank || '-'}위</span></div><div class="form">${t.form}</div><p>${t.brief}</p><div class="metric"><small>최근 지표</small><b>${t.recent_metric}</b></div>${t.news.map(n=>`<div class="newsItem">• ${n}</div>`).join('')}`;
    root.appendChild(el);
  })
}
function renderSchedule(){
  const root=$('#scheduleList'); root.innerHTML='';
  state.schedule.forEach(day=>{
    const el=document.createElement('section'); el.className='dayBlock';
    el.innerHTML=`<h3>${day.date_label}</h3><table class="scheduleTable"><thead><tr><th>시간</th><th>경기</th><th>구장</th><th>상태</th></tr></thead><tbody>${day.games.map(g=>`<tr><td>${g.time}</td><td>${g.away} vs ${g.home}</td><td>${g.stadium}</td><td>${g.status}</td></tr>`).join('')}</tbody></table>`;
    root.appendChild(el);
  })
}
function renderVerify(){
  const root=$('#verifyList'); root.innerHTML='';
  state.validation_log.forEach(v=>{
    const el=document.createElement('div'); el.className='verifyItem';
    el.innerHTML=`<b class="${v.status==='ok'?'ok':'warn'}">${v.status.toUpperCase()}</b> · ${v.target}<p>${v.message}</p><small>검증 단계: ${v.steps.join(' → ')}</small>`;
    root.appendChild(el);
  })
}
$$('.tab').forEach(btn=>btn.addEventListener('click',()=>{$$('.tab').forEach(b=>b.classList.remove('active'));$$('.panel').forEach(p=>p.classList.remove('active'));btn.classList.add('active');$('#'+btn.dataset.tab).classList.add('active')}));
loadData().catch(err=>{document.body.innerHTML='<pre>데이터 로딩 실패: '+err.message+'</pre>'});
