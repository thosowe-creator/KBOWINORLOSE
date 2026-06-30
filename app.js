const $ = (s, root = document) => root.querySelector(s);

function pct(x) { return `${Math.round(x * 100)}%`; }
function safeList(items, fallback = '업데이트 대기') {
  return (items && items.length ? items : [fallback]).map(v => `<li>${v}</li>`).join('');
}
function miniCard(title, lines) {
  return `<div class="mini-card"><strong>${title}</strong>${lines.map(l => `<small>${l}</small>`).join('')}</div>`;
}

async function loadData() {
  const res = await fetch(`./data/current.json?ts=${Date.now()}`);
  if (!res.ok) throw new Error('data/current.json을 불러오지 못했습니다.');
  return res.json();
}

function renderGame(game) {
  const t = $('#game-template').content.cloneNode(true);
  $('.venue', t).textContent = `${game.date} · ${game.time} · ${game.stadium}`;
  $('.matchup', t).textContent = `${game.awayTeam} vs ${game.homeTeam}`;
  $('.pick', t).textContent = game.prediction.pick;
  $('.away-team', t).textContent = game.awayTeam;
  $('.home-team', t).textContent = game.homeTeam;
  $('.away-prob', t).textContent = pct(game.prediction.awayWinProbability);
  $('.home-prob', t).textContent = pct(game.prediction.homeWinProbability);
  $('.away-bar', t).style.width = pct(game.prediction.awayWinProbability);
  $('.home-bar', t).style.width = pct(game.prediction.homeWinProbability);
  $('.scoreline', t).textContent = `예상 기대득점: ${game.awayTeam} ${game.prediction.awayExpectedRuns.toFixed(1)} - ${game.homeTeam} ${game.prediction.homeExpectedRuns.toFixed(1)}`;
  $('.key-factors', t).innerHTML = safeList(game.keyFactors);

  $('.pitchers', t).innerHTML = [
    miniCard(game.awayStarter.name, [
      `${game.awayTeam} 선발`,
      `시즌 ERA ${game.awayStarter.era ?? '-'} · WHIP ${game.awayStarter.whip ?? '-'}`,
      `최근 흐름: ${game.awayStarter.recentNote ?? '수집 대기'}`
    ]),
    miniCard(game.homeStarter.name, [
      `${game.homeTeam} 선발`,
      `시즌 ERA ${game.homeStarter.era ?? '-'} · WHIP ${game.homeStarter.whip ?? '-'}`,
      `최근 흐름: ${game.homeStarter.recentNote ?? '수집 대기'}`
    ])
  ].join('');

  $('.lineup-status', t).textContent = game.lineup.status === 'confirmed'
    ? '17시 이후 공식/보조 출처 검증을 통과한 확정 라인업입니다.'
    : '17시 전에는 최근 출전 흐름, 등말소, 선발 상대 좌우, 휴식 패턴으로 만든 예상 라인업입니다.';

  $('.lineups', t).innerHTML = [
    miniCard(`${game.awayTeam} ${game.lineup.status === 'confirmed' ? '확정' : '예상'} 라인업`, [`<ol class="lineup-list">${safeList(game.lineup.away, '라인업 수집 대기')}</ol>`]),
    miniCard(`${game.homeTeam} ${game.lineup.status === 'confirmed' ? '확정' : '예상'} 라인업`, [`<ol class="lineup-list">${safeList(game.lineup.home, '라인업 수집 대기')}</ol>`])
  ].join('');

  $('.roster-news', t).innerHTML = safeList(game.rosterNews, '등말소 및 주요 뉴스 수집 대기');
  const checks = game.verification?.checks ?? [];
  $('.verification', t).innerHTML = checks.map(c => `• ${c.name}: ${c.status} ${c.message ? `— ${c.message}` : ''}`).join('<br>');
  $('.report', t).textContent = game.report;
  return t;
}

loadData().then(data => {
  $('#data-status').textContent = data.statusText;
  $('#today-label').textContent = data.generatedAtKST;
  $('#verification-label').textContent = `전체 검증: ${data.verificationSummary}`;
  $('#notice').textContent = data.notice || '';
  const box = $('#games');
  data.games.forEach(g => box.appendChild(renderGame(g)));
}).catch(err => {
  $('#notice').textContent = `데이터 로딩 실패: ${err.message}`;
});
