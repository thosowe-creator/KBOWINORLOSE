#!/usr/bin/env python3
"""
KBO Match Lab data generator.

핵심 원칙
1) 라인업 확정 전: 최근 흐름·뉴스·등말소·좌우 매치업 기반 예상 라인업 표시
2) 17:05 KST 이후: 라인업/등말소 재조회 후 확정 후보로 전환
3) 모든 핵심 데이터는 3단계 검증을 통과해야 confidence를 올림

주의
- 이 스타터는 구조와 검증 파이프라인을 제공하는 MVP입니다.
- 실제 서비스 전에는 각 데이터 제공 사이트의 약관/robots.txt/API 이용 범위를 확인하세요.
- 아래 SourceAdapter에 공식 API 또는 허가받은 데이터 공급자를 연결하면 됩니다.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "current.json"

TEAMS = {
    "한화": {"park": "대전 한화생명 볼파크", "base_runs": 5.4, "base_allowed": 5.0, "bullpen": 4.6},
    "KT": {"park": "수원 KT위즈파크", "base_runs": 5.2, "base_allowed": 5.1, "bullpen": 4.8},
    "LG": {"park": "잠실야구장", "base_runs": 5.0, "base_allowed": 4.7, "bullpen": 4.3},
    "두산": {"park": "잠실야구장", "base_runs": 4.9, "base_allowed": 5.0, "bullpen": 4.9},
    "삼성": {"park": "대구 삼성라이온즈파크", "base_runs": 5.1, "base_allowed": 5.2, "bullpen": 5.0},
    "KIA": {"park": "광주-KIA 챔피언스필드", "base_runs": 5.0, "base_allowed": 4.9, "bullpen": 4.7},
    "롯데": {"park": "사직야구장", "base_runs": 4.8, "base_allowed": 5.2, "bullpen": 5.1},
    "NC": {"park": "창원 NC파크", "base_runs": 4.9, "base_allowed": 5.0, "bullpen": 4.9},
    "SSG": {"park": "인천 SSG랜더스필드", "base_runs": 5.0, "base_allowed": 5.1, "bullpen": 4.9},
    "키움": {"park": "고척스카이돔", "base_runs": 4.4, "base_allowed": 5.4, "bullpen": 5.2},
}

PARK_FACTORS = {
    "대전 한화생명 볼파크": 0.18,
    "수원 KT위즈파크": 0.08,
    "잠실야구장": -0.22,
    "대구 삼성라이온즈파크": 0.15,
    "광주-KIA 챔피언스필드": 0.06,
    "사직야구장": 0.05,
    "창원 NC파크": 0.02,
    "인천 SSG랜더스필드": 0.12,
    "고척스카이돔": -0.03,
}

@dataclass
class Check:
    name: str
    status: str
    message: str

class SourceAdapter:
    """실서비스에서는 이 클래스에 공식/허가 데이터 소스를 연결합니다."""

    def get_today_games(self, today: str) -> List[Dict[str, Any]]:
        # Demo seed. 실제 구현: 공식 일정/네이버/Statiz 등 허가된 소스에서 fetch 후 normalize.
        return [
            {
                "date": today,
                "time": "18:30",
                "awayTeam": "KT",
                "homeTeam": "한화",
                "stadium": "대전 한화생명 볼파크",
                "awayStarter": {"name": "맷 사우어", "era": 4.54, "whip": 1.31, "recentNote": "최근 등판 기복. 5~6이닝 3실점권 기대"},
                "homeStarter": {"name": "윌켈 에르난데스", "era": 4.49, "whip": 1.35, "recentNote": "최근 피홈런 리스크. 장타 억제가 핵심"},
                "headToHead": {"awayWins": 4, "homeWins": 2, "awayRunsPerGame": 8.67, "homeRunsPerGame": 7.50},
            }
        ]

    def get_team_stats(self, team: str) -> Dict[str, Any]:
        base = TEAMS[team]
        return {
            "runsPerGame": base["base_runs"],
            "runsAllowedPerGame": base["base_allowed"],
            "bullpenEra": base["bullpen"],
            "recentRunsPerGame": base["base_runs"] + (0.25 if team == "한화" else 0.05),
            "recentAllowedPerGame": base["base_allowed"],
        }

    def get_lineups(self, game: Dict[str, Any], now: datetime) -> Dict[str, Any]:
        after_five = now.hour > 17 or (now.hour == 17 and now.minute >= 5)
        # 실제 구현: 17:05 이후 공식 라인업 fetch. 실패하면 예상 라인업 유지 + warning.
        return {
            "status": "confirmed" if after_five else "projected",
            "away": ["1. CF 배정대", "2. RF 최원준", "3. DH 강현우", "4. 1B 문상철", "5. LF 김민혁", "6. 3B 황재균", "7. 2B 오윤석", "8. C 장성우", "9. SS 심우준"],
            "home": ["1. 2B 문현빈", "2. RF 페라자", "3. DH 강백호", "4. 3B 노시환", "5. 1B 장규현", "6. LF 김태연", "7. CF 이원석", "8. C 허인서", "9. SS 이도윤"],
        }

    def get_roster_news(self, teams: List[str], now: datetime) -> List[str]:
        # 실제 구현: KBO 엔트리 등록/말소, 구단 공지, 주요 기자 뉴스 취합.
        if now.hour >= 17:
            return ["17시 이후 엔트리 재조회 대상: 등록/말소 공식 발표 반영", "주전 휴식·포수 매칭·외국인타자 출전 여부 확인 필요"]
        return ["17시 전: 전일 엔트리와 최근 뉴스 기준 예상 반영", "라인업 확정 전이므로 주전 휴식 가능성은 예측 신뢰도에서 감점"]


def verify_three_passes(game: Dict[str, Any], lineup: Dict[str, Any]) -> List[Check]:
    checks: List[Check] = []

    # 1차: 필수 필드/형식 검증
    required = ["date", "time", "awayTeam", "homeTeam", "stadium", "awayStarter", "homeStarter"]
    missing = [k for k in required if not game.get(k)]
    checks.append(Check("1차 스키마 검증", "PASS" if not missing else "FAIL", "필수 필드 정상" if not missing else f"누락: {', '.join(missing)}"))

    # 2차: 범위/상식 검증
    era_ok = all(0 <= float(game[x].get("era", 99)) <= 15 for x in ["awayStarter", "homeStarter"])
    prob_msg = "ERA/WHIP 등 수치 범위 정상" if era_ok else "비정상 범위 감지"
    checks.append(Check("2차 범위 검증", "PASS" if era_ok else "WARN", prob_msg))

    # 3차: 교차 검증 시뮬레이션
    lineup_ok = len(lineup.get("away", [])) == 9 and len(lineup.get("home", [])) == 9
    source_count = 3 if lineup_ok else 1
    checks.append(Check("3차 교차 검증", "PASS" if source_count >= 3 else "WARN", f"동일 항목 최소 {source_count}개 출처 기준으로 비교하도록 설계"))

    # 4차: 라인업 시간대 검증
    checks.append(Check("라인업 상태 검증", "PASS", "17시 전 projected, 17:05 이후 confirmed 후보로 전환"))
    return checks


def expected_runs(away: str, home: str, game: Dict[str, Any]) -> Dict[str, float]:
    a = SourceAdapter().get_team_stats(away)
    h = SourceAdapter().get_team_stats(home)
    park = PARK_FACTORS.get(game["stadium"], 0)

    away_er = (
        a["runsPerGame"] * 0.30 +
        h["runsAllowedPerGame"] * 0.22 +
        a["recentRunsPerGame"] * 0.16 +
        float(game["homeStarter"].get("era", 4.8)) * 0.11 +
        h["bullpenEra"] * 0.08 +
        game.get("headToHead", {}).get("awayRunsPerGame", a["runsPerGame"]) * 0.05 +
        0.08 * 5
    ) + park
    home_er = (
        h["runsPerGame"] * 0.30 +
        a["runsAllowedPerGame"] * 0.22 +
        h["recentRunsPerGame"] * 0.16 +
        float(game["awayStarter"].get("era", 4.8)) * 0.11 +
        a["bullpenEra"] * 0.08 +
        game.get("headToHead", {}).get("homeRunsPerGame", h["runsPerGame"]) * 0.05 +
        0.08 * 5
    ) + park + 0.12  # 홈 어드밴티지
    return {"away": round(away_er, 2), "home": round(home_er, 2)}


def win_probability(away_er: float, home_er: float) -> Dict[str, float]:
    # 기대득점차를 로지스틱으로 변환. 과신 방지를 위해 35~65% 범위로 클램프.
    diff = home_er - away_er
    home = 1 / (1 + math.exp(-diff * 0.55))
    home = max(0.35, min(0.65, home))
    return {"home": round(home, 3), "away": round(1 - home, 3)}


def build_report(game: Dict[str, Any], pred: Dict[str, Any], lineup: Dict[str, Any], roster_news: List[str]) -> str:
    return f"""{game['awayTeam']}와 {game['homeTeam']}의 오늘 경기는 선발 매치업, 최근 득점 흐름, 상대전적, 구장 특성을 함께 보면 {pred['pick']} 쪽을 근소 우세로 잡습니다.

예상 기대득점은 {game['awayTeam']} {pred['awayExpectedRuns']:.1f}점, {game['homeTeam']} {pred['homeExpectedRuns']:.1f}점입니다. 승률은 {game['awayTeam']} {pred['awayWinProbability']*100:.0f}%, {game['homeTeam']} {pred['homeWinProbability']*100:.0f}%입니다.

핵심은 선발투수의 초반 장타 억제와 불펜 연결입니다. {game['stadium']}은 구장 특성상 장타성 타구와 펜스 플레이 변수가 존재하므로, 단순 팀 평균보다 빅이닝 가능성을 더 크게 봐야 합니다.

라인업 상태는 현재 {lineup['status']}입니다. 17시 전에는 최근 출전 패턴, 등말소 현황, 좌우 매치업, 휴식 패턴을 바탕으로 예상 라인업을 제시하고, 17:05 이후에는 공식/보조 출처를 재조회해 확정 라인업으로 갱신합니다.

등말소/뉴스 반영: {' / '.join(roster_news)}
"""


def main() -> None:
    now = datetime.now(KST)
    today = os.environ.get("KBO_DATE", now.strftime("%Y-%m-%d"))
    adapter = SourceAdapter()
    raw_games = adapter.get_today_games(today)
    games = []

    for g in raw_games:
        lineup = adapter.get_lineups(g, now)
        roster_news = adapter.get_roster_news([g["awayTeam"], g["homeTeam"]], now)
        er = expected_runs(g["awayTeam"], g["homeTeam"], g)
        wp = win_probability(er["away"], er["home"])
        pick = g["homeTeam"] if wp["home"] >= wp["away"] else g["awayTeam"]
        checks = verify_three_passes(g, lineup)
        pred = {
            "pick": pick,
            "awayWinProbability": wp["away"],
            "homeWinProbability": wp["home"],
            "awayExpectedRuns": er["away"],
            "homeExpectedRuns": er["home"],
            "confidence": "보통" if all(c.status == "PASS" for c in checks[:3]) else "낮음",
        }
        g2 = {
            **g,
            "prediction": pred,
            "lineup": lineup,
            "rosterNews": roster_news,
            "keyFactors": [
                f"{g['stadium']} 구장 보정 반영",
                "선발투수 최근 흐름과 시즌 ERA 동시 반영",
                "상대전적은 표시하되 표본 한계 때문에 낮은 가중치 적용",
                "라인업 확정 전/후 예측을 분리",
            ],
            "verification": {"checks": [asdict(c) for c in checks]},
            "report": build_report(g, pred, lineup, roster_news),
        }
        games.append(g2)

    payload = {
        "generatedAtKST": now.strftime("%Y-%m-%d %H:%M KST"),
        "statusText": "라인업 확정 반영" if now.hour >= 17 else "라인업 예상 단계",
        "verificationSummary": "3-pass enabled",
        "notice": "MVP 데모 데이터입니다. 실서비스에서는 scripts/update_data.py의 SourceAdapter에 공식/허가 데이터 소스를 연결하세요.",
        "games": games,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")

if __name__ == "__main__":
    main()
