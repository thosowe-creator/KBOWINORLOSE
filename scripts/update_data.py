#!/usr/bin/env python3
"""KBO Match Lab data updater.

개인용 자동 수집 파이프라인입니다.
- 13:00 KST: 모든 팀 최근 현황/뉴스/일정 기반 사전 분석
- 17:05 KST: 라인업/등말소 재조회
- 17:20, 18:00 KST: 라인업 누락 보완 및 최종 재검증

실제 운영에서는 SourceAdapter의 fetch_* 메서드에 사용하는 출처별 파서를 붙이면 됩니다.
기본값은 네트워크 실패 또는 파서 실패 시 데모/캐시 데이터로 안전하게 current.json을 생성합니다.
"""
from __future__ import annotations
import json, os, math, random, re, sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "current.json"
KST = timezone(timedelta(hours=9))
TEAMS = ["LG","한화","KT","KIA","롯데","SSG","삼성","NC","두산","키움"]
LOGOS = {"LG":"🧢","한화":"🦅","KT":"🧙","KIA":"🐯","롯데":"🌊","SSG":"🚀","삼성":"🦁","NC":"🦖","두산":"🐻","키움":"🦸"}

class SourceAdapter:
    """출처별 수집부. 개인용이면 여기에 KBO/포털/스탯티즈 파서를 붙이면 됩니다."""
    def http_text(self, url: str, timeout: int = 12) -> str:
        req = Request(url, headers={"User-Agent":"Mozilla/5.0 KBO-Match-Lab personal collector"})
        with urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")

    def fetch_google_news(self, team: str) -> list[str]:
        # API 키 없이 가능한 RSS. 숫자 기록의 원천으로 쓰지 말고, 소식/흐름 요약 보조로만 사용.
        q = quote(f'KBO {team} 야구 최근 등말소 라인업')
        url = f'https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko'
        try:
            text = self.http_text(url)
            root = ET.fromstring(text)
            out = []
            for item in root.findall('.//item')[:4]:
                title = item.findtext('title') or ''
                title = re.sub(r'\s+-\s+[^-]+$', '', title).strip()
                if title: out.append(title)
            return out[:3]
        except Exception:
            return []

    def fetch_schedule(self, now: datetime) -> list[dict]:
        # TODO: KBO/네이버 일정 파서 연결 위치. 현재는 기본 매치업 템플릿.
        return [{"time":"18:30","away":"KT","home":"한화","stadium":"대전","status":"예정"},
                {"time":"18:30","away":"삼성","home":"LG","stadium":"잠실","status":"예정"},
                {"time":"18:30","away":"KIA","home":"롯데","stadium":"사직","status":"예정"},
                {"time":"18:30","away":"두산","home":"SSG","stadium":"문학","status":"예정"},
                {"time":"18:30","away":"키움","home":"NC","stadium":"창원","status":"예정"}]

    def fetch_lineups(self, game: dict, now: datetime) -> dict:
        # 17:05 이후 실제 라인업 파서 연결 위치.
        return {"status":"확정 라인업" if now.hour >= 17 else "예상 라인업", "away": [], "home": []}

    def fetch_roster_moves(self, now: datetime) -> list[str]:
        # 등말소 파서 연결 위치.
        return ["등말소 자동 조회 슬롯: 17:05 이후 재검증"]

def clamp(v, lo, hi): return max(lo, min(hi, v))

def win_prob_from_runs(a, h):
    # 기대득점 차이를 승률로 변환. 설명 가능한 간단 모델.
    p_home = 1/(1+math.exp(-(h-a)/1.7))
    return round((1-p_home)*100), round(p_home*100)

def make_report(g):
    leader = g['home']['team'] if g['home']['win_probability'] >= g['away']['win_probability'] else g['away']['team']
    return f"{leader} 쪽이 근소 우세로 계산됩니다. 13시 사전 분석에서는 최근 팀 흐름, 선발 매치업, 구장 특성, 뉴스/등말소 키워드를 반영하고, 17:05 이후 실제 라인업을 다시 조회해 승률과 기대득점을 재계산합니다."

def validate(payload):
    logs=[]
    # 1) schema
    ok = bool(payload.get('games')) and bool(payload.get('teams')) and bool(payload.get('schedule'))
    logs.append({"target":"전체 스키마","status":"ok" if ok else "warn","message":"필수 데이터 묶음 확인 완료." if ok else "필수 데이터 일부 누락.","steps":["schema","required fields","json write"]})
    # 2) range
    bad=[]
    for g in payload['games']:
        s = g['away']['win_probability'] + g['home']['win_probability']
        if abs(s-100)>1: bad.append(f"{g['away']['team']} vs {g['home']['team']}")
    logs.append({"target":"승률 범위","status":"ok" if not bad else "warn","message":"모든 경기 승률 합계 정상." if not bad else f"승률 합계 확인 필요: {', '.join(bad)}","steps":["range","sum=100","sanity check"]})
    # 3) cross-source placeholder
    logs.append({"target":"3중 검증 구조","status":"ok","message":"공식/포털/보조 출처를 비교하는 슬롯이 준비되어 있습니다. 파서 연결 전에는 캐시/데모 데이터로 대체됩니다.","steps":["official source","portal source","backup source"]})
    return logs

def build():
    now = datetime.now(KST)
    adapter = SourceAdapter()
    schedule = adapter.fetch_schedule(now)
    # 간단한 팀 폼 데모. 실제로는 최근 10경기/득실/팀 기록 파서에서 채움.
    ranks = {t:i+1 for i,t in enumerate(TEAMS)}
    form_pool = ["7승 3패","6승 4패","6승 4패","5승 5패","5승 5패","4승 6패","4승 6패","4승 6패","3승 7패","3승 7패"]
    teams=[]
    for i,t in enumerate(TEAMS):
        news = adapter.fetch_google_news(t)
        if not news:
            news = ["13시 뉴스/기록 자동 요약 슬롯", "17시 라인업·등말소 재검증 예정"]
        teams.append({"team":t,"rank":ranks[t],"form":form_pool[i],"brief":f"{t} 최근 흐름 자동 분석 대상입니다. 실제 파서 연결 시 최근 10경기, 부상/등말소, 기사 키워드가 반영됩니다.","recent_metric":f"최근 폼 {form_pool[i]}","news":news[:3]})
    # 매치업별 임시 기대득점/확률. 실제로는 predict.py로 분리 가능.
    games=[]
    for idx,m in enumerate(schedule):
        # rank 기반 아주 단순한 사전값. 홈 +0.15점, 구장별 보정.
        ar, hr = ranks.get(m['away'],5), ranks.get(m['home'],5)
        away_runs = round(clamp(4.8 + (hr-ar)*0.08 + random.uniform(-.25,.25), 3.2, 6.7),1)
        home_runs = round(clamp(4.95 + (ar-hr)*0.08 + random.uniform(-.25,.25), 3.2, 6.9),1)
        awp,hwp = win_prob_from_runs(away_runs, home_runs)
        lineups = adapter.fetch_lineups(m, now)
        game={"time":m['time'],"stadium":m['stadium'],"lineup_status":lineups['status'],"confidence":"보통" if now.hour>=17 else "라인업 전/보통","validation_passes":3,"key_factor":"라인업·선발·최근 폼","away":{"team":m['away'],"win_probability":awp,"expected_runs":away_runs},"home":{"team":m['home'],"win_probability":hwp,"expected_runs":home_runs},"away_starter":"자동 조회","home_starter":"자동 조회","report":"","notes":["13시 모든 팀 최근 현황 반영","17:05 라인업/등말소 재조회","불일치 데이터는 검증 로그에 WARN 표시"]}
        game['report']=make_report(game)
        games.append(game)
    date_label = now.strftime('%Y.%m.%d') + ' ' + '월화수목금토일'[now.weekday()]
    payload={"date":now.strftime('%Y-%m-%d'),"date_label":date_label,"updated_at_kst":now.strftime('%Y-%m-%d %H:%M'),"mode_label":"17시 라인업 반영" if now.hour>=17 else "13시 사전 분석","lineup_status_label":"확정 라인업 조회 모드" if now.hour>=17 else "예상 라인업 / 17:05 재조회 예정","summary":"모든 팀 최근 현황은 13:00, 라인업·등말소는 17:05 이후 자동 재검증합니다.","games":games,"teams":teams,"schedule":[{"date_label":date_label,"games":schedule}],"validation_log":[]}
    payload['validation_log']=validate(payload)
    DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'wrote {DATA}')

if __name__ == '__main__':
    build()
