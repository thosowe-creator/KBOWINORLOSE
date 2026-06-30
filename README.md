# KBO Match Lab

개인용 KBO 승패예측/전력분석 대시보드입니다.

## 반영된 것

- 모든 경기 승률을 한눈에 보는 카드 UI
- 날짜/업데이트 상태 표시
- 오늘 분석 / 팀 최근 현황 / KBO 일정 / 검증 로그 탭
- 매일 13:00 KST 모든 팀 최근 현황 자동 분석 슬롯
- 17:05, 17:20, 18:00 KST 라인업·등말소 재조회 슬롯
- GitHub Pages 정적 페이지 + GitHub Actions 자동 데이터 갱신
- 최소 3단계 검증 로그 구조

## 사용법

1. 이 폴더를 GitHub 저장소에 업로드
2. Settings → Pages → Deploy from branch → main / root
3. Actions 권한에서 Workflow write 권한 허용
4. `.github/workflows/update-data.yml`가 자동으로 `data/current.json`을 갱신

## 실제 데이터 소스 연결 위치

`scripts/update_data.py`의 `SourceAdapter`에 출처별 파서를 붙이면 됩니다.

- `fetch_schedule()` : KBO 일정
- `fetch_lineups()` : 17시 이후 라인업
- `fetch_roster_moves()` : 등말소
- `fetch_google_news()` : 뉴스/최근 현황 보조

현재 기본값은 네트워크/파서 실패 시에도 화면이 깨지지 않도록 데모/캐시 데이터로 `current.json`을 생성합니다.

## 추천 운영 방식

개인용이면 숫자 기록은 크롤러가 가져오고, AI는 검증된 데이터를 바탕으로 리포트 문장을 작성하게 하는 구조가 가장 안정적입니다.
