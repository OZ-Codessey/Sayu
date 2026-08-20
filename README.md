

<div align="center">

# S A Y U
<h2 style="font-size: 28px; letter-spacing: 2px;">
  <ruby style="ruby-position: under;">自<rt style="font-size: 30%; color: #8A8D8F;">자</rt></ruby><ruby style="ruby-position: under;">然<rt style="font-size: 30%; color: #8A8D8F;">연</rt></ruby>과 
  <ruby style="ruby-position: under;">建<rt style="font-size: 30%; color: #8A8D8F;">건</rt></ruby><ruby style="ruby-position: under;">築<rt style="font-size: 30%; color: #8A8D8F;">축</rt></ruby>의 
  <ruby style="ruby-position: under;">餘<rt style="font-size: 30%; color: #8A8D8F;">여</rt></ruby><ruby style="ruby-position: under;">情<rt style="font-size: 30%; color: #8A8D8F;">정</rt></ruby>
</h2>

> *"침묵 속에서 거장의 철학과 자연의 원형을 마주하다"*

---

</div>

자연 원형과 국내외 거장의 건축·조경·예술이 어우러진 국내 사유(思惟) 여행지를 **Google Gemini**가 엄선하고, **카카오 로컬 API**로 실시간 맛집을 결합하여 한 편의 감각적인 마크다운 여행 리포트로 완성하는 CLI 프로그램입니다.

---





<br><br>
# Overview
사유(思惟) 여행 큐레이션
자연 원형과 국내외 거장의 건축·조경·예술이 어우러진 국내 사유(思惟) 여행지를
LLM(Gemini)이 추천하고, 카카오 로컬 API로 실시간 맛집을 결합하여
한 편의 마크다운 여행 리포트로 완성하는 CLI 프로그램입니다.

**큐레이팅 로직은 여행 날짜를 입력하면 다음 3단계 파이프라인이 순서대로 실행됩니다.**

```
[1/3] Gemini API — 계절에 맞는 사유 명소 2~3곳 1차 추천 
[2/3] Kakao API — 위 3도시의 위치기반 맛집 최대 5곳 검색
[3/3] Gemini API — 1차 맛집 추천지를 2차 llm기반 엄선 및 명소 + 에러 로그를 종합한 최종 마크다운 리포트 생성
```

---



| 항목 | 내용 |
| :--- | :--- |
| 목적 | 여행 날짜 하나만 입력하면 계절에 맞는 사유 여행지와 맛집을 자동으로 큐레이션 |
| LLM API | Google Gemini (`gemini-3.5-flash`) |
| 지도/장소 API | Kakao Local (키워드 기반 맛집 검색) |
| 실행 환경 | Python 3.12+ , 터미널(CLI) 전용 |
| 핵심 특징 | JSON 파싱 실패 1회 자동 재시도, 지도 API 실패 시 비차단 처리, 결과 캐싱(0-Token 재실행) |


<br><br>

# How To Run

###  준비

```bash
## 1) 저장소 클론 
git clone https://github.com/OZ-Codessey/Sayu.git

# 2) 의존성 라이브러리 설치
pip3 install -r requirements.txt

# 3) 환경변수 파일 생성 및 API 키 설정
cp .env.example .env
```

### API 키 설정 방법

>❗이 프로그램은 두 가지 API 키가 필요합니다.  

| 환경변수명 | 발급처 | 용도 |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) | 1차 명소 추천 / 2차 1일 일정 맛집 엄선 및 최종 리포트 생성 |
| `KAKAO_REST_API_KEY` | [Kakao Developers](https://developers.kakao.com) | 도시별 맛집 검색 (카카오 로컬 API) |

### 세부 설정 절차

1. 프로젝트 루트의 `.env.example` 파일을 복사해 `.env` 파일을 만듭니다.
   ```bash
   cp .env.example .env
   ```
2. `.env` 파일을 열어 발급받은 키를 채워 넣습니다.
   ```
   GEMINI_API_KEY="your_gemini_api_key"
   KAKAO_REST_API_KEY="your_kakao_rest_api_key"
   ```
3. 두 키 중 하나라도 비어 있으면, 프로그램 실행 즉시 아래와 같은 안내와 함께 종료됩니다.
   ```
   ❌ AUTH ERROR  필수 API 키가 환경변수에 설정되지 않았습니다.
   누락된 키 : GEMINI_API_KEY, KAKAO_REST_API_KEY
   ```

### 실행

```bash
python3 travel_planner.py --date "YYYY-MM-DD"

[예시]
python3 travel_planner.py --date "2026-10-25"

```
### 👁️ 결과물 확인 방법

>정상 실행이 완료되면 `results/` 폴더가 자동 생성되고, 아래 두 파일에서 확인합니다.

```
results/
├── travel_plan_2026-10-25.json     # 원본 데이터 (1차 추천 + 맛집 검색 결과 + 에러 로그)
└── travel_report_2026-10-25.md     # 최종 여행 리포트 (마크다운)
```

- **`travel_plan_{날짜}.json`**: `curation_result`(1차 추천), `restaurant_results`(맛집 검색 결과), `errors`(오류 요약)를 포함한 원본 데이터입니다.
- **`travel_report_{날짜}.md`**: 추천 지역, 추천 이유, 날씨, 행사, 맛집, 1일 일정, 오류 요약까지 포함한 최종 리포트입니다. 마크다운 뷰어(VS Code, GitHub 등)에서 바로 확인할 수 있습니다.
- 리포트는 프로그램 실행 완료 시 콘솔에도 동일하게 출력됩니다.
- **동일한 날짜로 재실행**하면 저장된 결과를 그대로 불러와 즉시 출력하며(0-Token 캐시), 외부 API를 다시 호출하지 않습니다.

---

## ⚠️ 보안 주의 사항 (API 키 유출 방지)

- API 키는 코드나 README에 절대 직접 작성하지 않으며, `.env` 파일 또는 환경변수로만 관리합니다.
- `.env` 파일은 `.gitignore`에 등록되어 있어 Git에 커밋되지 않습니다. 커밋 전 `git status`로 `.env`가 추적 대상에 포함되지 않았는지 반드시 확인하세요.
- 저장소에는 실제 키가 없는 `.env.example`(템플릿)만 포함되어 있습니다.
- `results/` 폴더의 JSON/MD 결과물에는 API 키가 포함되지 않지만, 공개 저장소에 업로드하기 전에는 개인 식별 정보가 없는지 한 번 더 확인하는 것을 권장합니다.
- 키가 실수로 노출된 경우, 즉시 발급처(Google AI Studio / Kakao Developers)에서 키를 재발급(rotate)하세요.

---
<br>

## 🔍 커밋 히스토리

| 커밋 번호 | 기능 단위 (Feature Unit) | Commit Message (English) | 교안 요구사항 / 에러 방어 / 보너스 매핑 |
| :--- | :--- | :--- | :--- |
| **Commit 1** | 저장소 초기화 | `feat: Initial commit` | 기본 저장소 생성 및 초기 파일 구성 |
| **Commit 2** | 보안 및 환경 의존성 정의 | `chore: set up security configs and dependencies` | API 키 유출 방지 및 실행 환경 패키지 정의 |
| **Commit 3** | CLI 날짜 파싱 및 유효성 검증 | `feat: implement CLI argument parsing and date validation` | 잘못된 날짜 포맷/미존재 날짜 입력 시 안내 후 즉시 종료 (`sys.exit(1)`) |
| **Commit 4** | API 키 환경변수 보안 검증 | `feat: implement API key security validation for Gemini and Kakao` | **[에러 방어 1]** `GEMINI_API_KEY`, `KAKAO_REST_API_KEY` 부재 시 즉시 종료 및 설정 방법 안내 |
| **Commit 5** | 복수 지역 프롬프트 및 LLM 기본 호출 | `feat: establish multi-city contemplation travel curation and harden date/schema validation` ([보너스 1]) | **[보너스 1]** 사유 여행 2~3곳 복수 추천 프롬프트 구축, 과거 날짜 입력 차단([오류 방어 1-1]), AFC 비활성화를 통한 SDK 경고 원천 차단 및 프롬프트 고도화 |
| **Commit 6** | JSON 파싱 검증 및 재시도 로직 | `feat: add schema validation and automated retry pipeline for LLM curation` | **[에러 방어 2]** LLM JSON 파싱 실패 시 프롬프트 보정 후 1회 재시도 방어 로직 구현. 파이프라인 전역 에러(`errors`) 누적 관리 기반 마련 |
| **Commit 7** | 카카오 지도 복수 지역 맛집 검색 | `feat: connect Kakao local API for multi-city restaurant search` | 카카오 로컬 API 연동, 복수 도시에 대한 맛집 5곳의 필수 메타데이터(장소명, 주소, 좌표, URL 등) 추출·구조화 |
| **Commit 8** | 지도 API 오류 격리 및 폴백 처리 | `fix(defense): add non-blocking error isolation for place search` | **[에러 방어 3]** 401/403 인증, 네트워크 타임아웃, 0건 검색 시 '데이터 없음' 처리 후 프로그램 중단 없이 진행 |
| **Commit 9** | LLM 기반 최종 마크다운 리포트 생성 | `feat: final markdown report generation via 2nd-stage LLM reasoning` | 1차 건축 명소와 카카오 맛집 데이터를 결합해 LLM에 2차 주입, 도시별 1일 일정 구성 및 맛집 최종 엄선. 리포트 하단에 에러 요약 통합 |
| **Commit 10** | 듀얼 파일 저장 및 결과 캐싱 | `feat: implement dual file exporter and raw data caching mechanism` | **[보너스 2]** `results/` 폴더 내 원본 JSON 및 MD 저장, 동일 날짜 재실행 시 캐시 로드(0-Token) |
| **Commit 11** | 실행 및 아키텍처 문서화 | `docs: add README with setup guide, usage, and API key security notes` | 프로그램 개요·실행법·API 키 설정법·결과 확인법 작성 |

---




🌲 파일 구조도  
```
Sayu/
├── .env.example                                      # API 키 템플릿 파일
├── .gitignore                                        # Git 추적 제외 설정 파일 (.env 등 은닉)
├── README.md                                         # 프로젝트 소개 및 실행 가이드 문서
├── requirements.txt                                  # 프로젝트 필수 의존성 패키지 목록
├── travel_planner.py                                 # 사유(思惟) 여행 큐레이션 CLI 메인 실행 스크립트
│
├── records/                                          # 개발 및 단계별 테스트 
└── results/                                          # CLI 실행 시 자동 생성되는 최종 결과물 저장소
    ├── curation_report_2026-10-25.md                 # 큐레이션 최종 마크다운 리포트
    └── curation_result_2026-10-25.json               # 1차 추천 및 카카오 맛집 통합 원본 JSON 데이터
```

<br>

### 🏛️ S A Y U : 自然과 建築의 餘情
> **[ 思惟(사유) 여행 큐레이션 ]**
> 
> *"침묵 속에서 거장의 철학과 자연의 원형을 마주하다"*
> 
> ---
> * **旅程 日字** │ `2026-10-25`
> * **季節 테마** │ 가을 풍설기천년 — 천년의 모과빛

