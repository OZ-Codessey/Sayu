# ==============================================================================
# [Imports & Dependencies] 필수 라이브러리 및 커밋별 사용 내역
# ==============================================================================
import argparse                 # [Commit 3] CLI 인자(--date) 파싱 및 표준 도움말 지원
import json                     # [Commit 5/6/10] 템플릿 직렬화, 파싱 검증 및 JSON 원본 캐시 파일 저장/로드
import os                       # [Commit 4/10] 환경변수 조회 및 results/ 디렉터리 자동 생성/캐시 파일 확인
import sys                      # [Commit 3] 유효성 검증 실패 시 예외 종료 (sys.exit)
from datetime import datetime   # [Commit 3] 날짜 유효성 검증 및 계절 테마 판별
from dotenv import load_dotenv  # [Commit 4] .env 파일 환경변수 로드

# [Commit 5/9] Google GenAI SDK (1차 추천 및 최종 종합 리포트 생성)
from google import genai
from google.genai import types
from google.genai.errors import APIError  # [Commit 6] LLM 통신/서버 에러 방어용

# [Commit 7] 카카오 로컬 REST API 통신용 라이브러리 (pip install requests)
# [Commit 8] 카카오 API 세부 HTTPError / Timeout / ConnectionError 예외 격리용
import requests


# ==============================================================================
# [Design System] 자연과 건축의 여정 (ANSI 색채 & 타이포그래피)
# ==============================================================================
class Style:
    RESET       = "\033[0m"
    BOLD        = "\033[1m"
    DIM         = "\033[2m"
    ITALIC      = "\033[3m"
    UNDERLINE   = "\033[4m"

    ORANGE      = "\033[38;5;208m"
    BURNT_ORANGE= "\033[38;5;166m"
    YELLOW      = "\033[38;5;220m"
    FOREST_GRN  = "\033[38;5;35m"
    SPRING_GRN  = "\033[38;5;119m"
    WATER_BLUE  = "\033[38;5;74m"
    CONCRETE    = "\033[38;5;246m"
    DARK_GRAY   = "\033[38;5;240m"
    WHITE       = "\033[38;5;255m"
    SUCCESS_GRN = "\033[1m\033[38;5;71m"

    BG_BURNT    = "\033[48;5;166m\033[38;5;232m\033[1m"
    BG_WARN     = "\033[48;5;214m\033[38;5;232m\033[1m"
    BG_RED      = "\033[48;5;196m\033[38;5;255m\033[1m"
    BG_CACHE    = "\033[48;5;34m\033[38;5;232m\033[1m"  # [Commit 10] 캐시 적중 전용 강조 배경


# ==============================================================================
# [Commit 3] 계절 테마 판별, 배너 출력 및 CLI 유효성 검증 [오류 방어 1-1]
# ==============================================================================
def get_seasonal_theme(date_str: str) -> tuple[str, str]:
    """
    [Commit 3] 날짜(월)를 분석하여 사유원 전용 계절별 테마와 색상을 반환합니다.
    """
    try:
        month = datetime.strptime(date_str, "%Y-%m-%d").month
    except ValueError:
        month = 10

    if month in [3, 4, 5]:
        return "봄-시자의 하얀 목련과 태초의 정원", Style.ORANGE
    elif month in [6, 7, 8]:
        return "여름 별유동천-백일간의 붉음과 물의 사유", Style.ORANGE
    elif month in [9, 10, 11]:
        return "가을 풍설기천년-천년의 모과 동산", Style.ORANGE
    else:
        return "겨울 고송-오래도록 홀로 푸르른 솔과 노출 콘크리트", Style.ORANGE


def get_season_key(date_str: str) -> str:
    """
    [Commit 5] 날짜(월)를 분석하여 코스 조회용 계절 키를 반환합니다.
    """
    try:
        month = datetime.strptime(date_str, "%Y-%m-%d").month
    except ValueError:
        month = 10

    if month in [3, 4, 5]:
        return "봄"
    elif month in [6, 7, 8]:
        return "여름"
    elif month in [9, 10, 11]:
        return "가을"
    else:
        return "겨울"


def print_banner(date_str: str):
    """
    [Commit 3] 콘솔 브랜딩 헤더 배너를 출력합니다.
    """
    theme_text, theme_color = get_seasonal_theme(date_str)
    header_title = (
        f"{Style.BOLD}{Style.WHITE}[ {Style.FOREST_GRN}사유(思惟){Style.WHITE} 여행 큐레이션 ]{Style.RESET}"
    )

    print(f"\n{Style.BG_BURNT}  자연과 건축의 여정  {Style.RESET} {header_title}")
    print(f"{Style.DARK_GRAY}──────────────────────────────────────────────────────────────────{Style.RESET}")
    print(f" {Style.CONCRETE}📅 여행 일자 :{Style.RESET} {Style.BOLD}{Style.ORANGE}{date_str}{Style.RESET}  │  "
          f"{Style.CONCRETE}🎨 계절 테마 :{Style.RESET} {Style.ITALIC}{theme_color}{theme_text}{Style.RESET}")
    print(f"{Style.DARK_GRAY}──────────────────────────────────────────────────────────────────{Style.RESET}\n")


def parse_arguments() -> argparse.Namespace:
    """
    [Commit 3] CLI 명령줄 옵션을 파싱합니다. (--date 필수)
    """
    parser = argparse.ArgumentParser(
        description="거장의 건축과 보존된 자연 원형 기반 사유(思惟) 여행 큐레이션 도구",
        usage="python travel_planner.py --date \"YYYY-MM-DD\""
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="여행 날짜 (YYYY-MM-DD 형식, 필수)"
    )
    return parser.parse_args()


def validate_date(date_str: str) -> str:
    """
    [Commit 3 / 오류 방어 1-1] 날짜 형식, 실존 여부 및 오늘 이후 날짜 검증
    """
    date_format = "%Y-%m-%d"
    try:
        valid_date = datetime.strptime(date_str, date_format).date()
        today = datetime.now().date()

        if valid_date < today:
            print(f"\n{Style.BG_RED} ❌ DATE ERROR {Style.RESET} {Style.BOLD}{Style.ORANGE}여행 날짜는 오늘({today}) 이후로 입력해 주세요.{Style.RESET}")
            print(f"   {Style.CONCRETE}입력된 날짜 : {date_str} (과거 날짜){Style.RESET}")
            print(f"   {Style.YELLOW}💡 올바른 사용법: python travel_planner.py --date \"YYYY-MM-DD\" (예: {today}){Style.RESET}\n")
            sys.exit(1)

        return valid_date.strftime(date_format)
    except ValueError:
        print(f"\n{Style.BG_RED} ❌ INPUT ERROR {Style.RESET} {Style.BOLD}{Style.ORANGE}날짜 형식이 올바르지 않거나 유효하지 않은 날짜입니다.{Style.RESET}")
        print(f"   {Style.CONCRETE}입력값 : {date_str}{Style.RESET}")
        print(f"   {Style.YELLOW}💡 올바른 사용법: python travel_planner.py --date \"YYYY-MM-DD\" (예: 2026-10-25){Style.RESET}\n")
        sys.exit(1)


# ==============================================================================
# [Commit 4 / 오류 방어 1-2] API 키 환경변수 보안 검증
# ==============================================================================
def check_api_keys() -> tuple[str, str]:
    """
    [Commit 4 / 오류 방어 1-2] Gemini 및 Kakao API 키의 .env 로드 여부를 검증합니다.
    """
    load_dotenv()

    gemini_key = os.getenv("GEMINI_API_KEY")
    kakao_key = os.getenv("KAKAO_REST_API_KEY")

    missing_keys = []
    if not gemini_key:
        missing_keys.append("GEMINI_API_KEY")
    if not kakao_key:
        missing_keys.append("KAKAO_REST_API_KEY")

    if missing_keys:
        print(f"\n{Style.BG_RED} ❌ AUTH ERROR {Style.RESET} {Style.BOLD}{Style.ORANGE}필수 API 키가 환경변수에 설정되지 않았습니다.{Style.RESET}")
        print(f"   {Style.CONCRETE}누락된 키 : {', '.join(missing_keys)}{Style.RESET}")
        print(f"   {Style.YELLOW}💡 설정 방법: 프로젝트 루트의 .env 파일에 아래 내용을 작성해 주세요.{Style.RESET}")
        print(f"      {Style.DIM}GEMINI_API_KEY=\"your_gemini_api_key\"{Style.RESET}")
        print(f"      {Style.DIM}KAKAO_REST_API_KEY=\"your_kakao_rest_api_key\"{Style.RESET}\n")
        sys.exit(1)

    return gemini_key, kakao_key


# ==============================================================================
# [Commit 5 / Commit 6] Gemini 1차 복수 추천 호출 (System Prompt & User Prompt 분리)
# ==============================================================================
def build_curation_user_prompt(date_str: str, is_retry: bool = False) -> str:
    """
    [Commit 5/6] 1차 여행지 추천용 User Prompt 구성 (스켈레톤 구조 템플릿 적용)
    """
    season_key = get_season_key(date_str)
    theme_text, _ = get_seasonal_theme(date_str)

    dynamic_schema_template = {
        "recommended_cities": [
            {
                "city_name": "지역명(시/군/구 단위 문자열)",
                "main_attraction": "거장의 철학이 담긴 대표 사유 명소 이름",
                "master_designer": "해당 공간을 설계/조경/창작한 거장 이름",
                "weather": f"{season_key}철 해당 지역의 기후 및 정취 요약",
                "events": ["추천 산책/사유 포인트 1", "추천 산책/사유 포인트 2"],
                "reason": "해당 공간의 건축 철학과 자연이 선사하는 사유의 가치 서술 (2~3문장)"
            }
        ]
    }

    retry_instruction = ""
    if is_retry:
        retry_instruction = (
            "\n[⚠️ 재시도 경고]\n"
            "이전 응답이 JSON 스키마 규격을 충족하지 못했습니다.\n"
            "반드시 'recommended_cities' 배열 키와 그 내부에 'city_name', 'main_attraction', "
            "'master_designer', 'weather', 'events', 'reason' 키를 모두 포함한 순수 JSON만 반환하세요.\n"
        )

    user_prompt = f"""
{retry_instruction}
[여행 정보]
- 여행 일자: {date_str} ({season_key}철)
- 참고용 계절 테마: {theme_text}

[요청 사항]
대중적 유흥지와 제주도를 배제하고, 자연 원형과 거장의 건축 미학이 살아 숨쉬는 국내 사유 명소 2~3곳(권장 3곳)을 선정하여 아래 JSON 스키마 규격으로 반환하세요.
- 군위 사유원은 고유한 계절 정취를 지닌 사유 명소로서 우선 검토 후보로 고려할 수 있습니다.
- 사유원 외에도 전국 전역에 위치한 자연원형이 살아 있고 내외부에 국내외 유명 거장들의 작품과 예술품을 자연과 함께 사유할 수 있는 공간 중 이번 {season_key}철 여행에 가장 어울리는 장소들을 다채롭게 구성해 주세요.

[반환할 JSON 구조 스키마]
{json.dumps(dynamic_schema_template, ensure_ascii=False, indent=2)}
"""
    return user_prompt


def call_gemini_multi_city_recommendation(date_str: str, api_key: str, is_retry: bool = False) -> str:
    """
    [Commit 5/6] Gemini LLM 1차 여행지 추천 호출 함수
    """
    client = genai.Client(api_key=api_key)

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │ 📜 [System Prompt (System Instruction)] - 1차 명소 발굴                 │
    # │ 사유 건축 큐레이터 페르소나 및 추천 배제/필수 원칙 규정                │
    # └────────────────────────────────────────────────────────────────────────┘
    system_prompt = (
        "당신은 인파로 붐비는 대중 상업 유흥 관광지를 철저히 배제하고, "
        "'보존된 자연 원형'과 '국내외 거장의 건축·조경·예술'이 융합된 침묵과 사색의 공간만을 큐레이션하는 '사유(思惟) 건축 전문 큐레이터'입니다.\n\n"
        "[추천 배제 기준]\n"
        "- 부산(해운대/광안리), 강릉(경포대), 제주도 전역, 속초, 여수 등 전형적인 상업 유흥 밀집지는 일절 배제합니다.\n\n"
        "[추천 필수 원칙]\n"
        "1. 승효상, 알바로 시자, 안도 타다오, 제임스 터렐, 김수근, 이타미 준, 정영선(조경가), 마리오 보타, 페터 춤토르, 민현식, 우규승 등 "
        "'실제 국내외 거장 건축가·조경가·공간예술가가 설계/참여하여 자연과 조화를 이루는 고유한 사유 공간'을 2~3곳(권장 3곳) 엄선하세요.\n"
        "2. 군위 사유원은 대표적인 사유 공간으로서 최우선 검토 대상에 포함할 수 있습니다.\n"
        "3. JSON 스키마의 'master_designer' 필드를 반드시 명시하고, 오직 순수한 JSON 문자열만 반환하세요."
    )

    # 1차 명소 추천을 위한 높은 창의성/다양성 설정 (온도 0.85, top_p 0.95)
    config = types.GenerateContentConfig(
        temperature=0.85,
        top_p=0.95,
        response_mime_type="application/json",
        system_instruction=system_prompt,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    user_prompt = build_curation_user_prompt(date_str, is_retry=is_retry)
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=user_prompt,
        config=config
    )
    return response.text


# ==============================================================================
# [Commit 6 / 오류 방어 2] JSON 스키마 검증 및 1회 자동 재시도 파이프라인
# ==============================================================================
def validate_recommendation_schema(data: dict) -> tuple[bool, str]:
    """
    [Commit 6 / 오류 방어 2] 1차 추천 JSON 데이터의 필수 스키마 구조를 검증합니다.
    """
    if not isinstance(data, dict):
        return False, "최상위 데이터가 JSON Object(dict) 형식이 아닙니다."

    cities = data.get("recommended_cities")
    if not isinstance(cities, list) or len(cities) == 0:
        return False, "'recommended_cities' 배열이 누락되었거나 비어 있습니다."

    required_keys = ["city_name", "main_attraction", "weather", "events", "reason"]
    for idx, city in enumerate(cities):
        if not isinstance(city, dict):
            return False, f"장소 [{idx + 1}] 데이터가 객체 형식이 아닙니다."
        for key in required_keys:
            if key not in city or not str(city[key]).strip():
                return False, f"장소 [{idx + 1}]의 필수 필드 '{key}' 누락 또는 빈 값입니다."
        if not isinstance(city.get("events"), list):
            return False, f"장소 [{idx + 1}]의 'events' 필드가 리스트 형식이 아닙니다."

    return True, "OK"


def get_curated_recommendations_with_retry(date_str: str, api_key: str, errors: list) -> dict:
    """
    [Commit 6 / 오류 방어 2] LLM 응답을 파싱/검증하고 실패 시 최대 1회 재시도합니다. (네트워크/서버 에러 방어 포함)
    """
    print(f" {Style.BURNT_ORANGE}[1/3] 1차 여행지 추천 생성 중 ...{Style.RESET}")

    # 1차 시도 (API 통신 및 파싱)
    try:
        raw_text = call_gemini_multi_city_recommendation(date_str, api_key, is_retry=False)
    except Exception as api_err:
        print(f"\n{Style.BG_RED} ❌ NETWORK / SERVER ERROR {Style.RESET} {Style.BOLD}{Style.ORANGE}Gemini API 서버 통신 실패 (일시적 과부하 또는 네트워크 장애){Style.RESET}")
        print(f"   {Style.CONCRETE}에러 내용 : {api_err}{Style.RESET}")
        print(f"   {Style.YELLOW}💡 조치 방법 : 잠시 후(10~20초 뒤) 다시 명령어를 실행해 주세요.{Style.RESET}\n")
        errors.append({"step": "llm_recommendation_api_call", "type": "SERVER_OR_NETWORK_ERROR", "message": str(api_err)})
        sys.exit(1)

    try:
        parsed_data = json.loads(raw_text)
        is_valid, msg = validate_recommendation_schema(parsed_data)
        if is_valid:
            return parsed_data
        else:
            raise ValueError(f"스키마 규격 불일치 ({msg})")
    except (json.JSONDecodeError, ValueError) as first_err:
        print(f"\n   {Style.BG_WARN} ⚠️ SCHEMA WARNING {Style.RESET} {Style.BOLD}{Style.YELLOW}1차 JSON 파싱/스키마 검증 실패{Style.RESET}")
        print(f"      {Style.CONCRETE}오류 내용 : {first_err}{Style.RESET}")
        print(f"      {Style.YELLOW}💡 조치 사항 : 프롬프트 스키마를 보정하여 1회 자동 재시도를 진행합니다...{Style.RESET}\n")
        errors.append({"step": "llm_recommendation_retry_1", "type": "PARSE_OR_SCHEMA_ERROR", "message": str(first_err)})

    # 2차 시도 (재시도 프롬프트 주입)
    try:
        raw_text_retry = call_gemini_multi_city_recommendation(date_str, api_key, is_retry=True)
    except Exception as api_retry_err:
        print(f"\n{Style.BG_RED} ❌ NETWORK ERROR {Style.RESET} {Style.BOLD}{Style.ORANGE}2차 재시도 중 네트워크/서버 오류 발생{Style.RESET}")
        print(f"   {Style.CONCRETE}에러 내용 : {api_retry_err}{Style.RESET}\n")
        errors.append({"step": "llm_recommendation_retry_api_call", "type": "SERVER_OR_NETWORK_ERROR", "message": str(api_retry_err)})
        sys.exit(1)

    try:
        parsed_data_retry = json.loads(raw_text_retry)
        is_valid, msg = validate_recommendation_schema(parsed_data_retry)
        if is_valid:
            print(f"   {Style.SUCCESS_GRN}✔ 2차 재시도를 통해 올바른 JSON 스키마 규격 복구 완료{Style.RESET}")
            return parsed_data_retry
        else:
            raise ValueError(f"2차 재시도 스키마 검증 실패 ({msg})")
    except (json.JSONDecodeError, ValueError) as second_err:
        print(f"\n{Style.BG_RED} ❌ FATAL ERROR {Style.RESET} {Style.BOLD}{Style.ORANGE}LLM 추천 결과 JSON 복구 실패 (최대 재시도 초과){Style.RESET}")
        print(f"   {Style.CONCRETE}최종 오류 : {second_err}{Style.RESET}")
        print(f"   {Style.YELLOW}💡 조치 방법 : LLM API 상태 또는 프롬프트 응답 형식을 확인해 주세요.{Style.RESET}\n")
        errors.append({"step": "llm_recommendation_fatal", "type": "FINAL_PARSE_FAIL", "message": str(second_err)})
        sys.exit(1)


# ==============================================================================
# [Commit 7] 카카오 로컬 REST API 기반 다중 도시 맛집 검색 파이프라인
# 및 [Commit 8 / 오류 방어 3] 401·403 권한·타임아웃·0건(데이터 없음) 비차단(Non-blocking) 예외 격리
# ==============================================================================
def fetch_kakao_restaurants_by_city(city_name: str, kakao_api_key: str, size: int = 5) -> list[dict]:
    """
    [Commit 7 / 과제 공통 조건] 단일 도시에 대한 카카오 로컬 키워드 검색 API 호출
    - 검색 키워드: '{city_name} 맛집'
    - 카테고리 필터: 음식점(FD6)
    - 필수 추출 필드: place_name, address, road_address, lat, lng(x/y), url, phone
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {kakao_api_key}"
    }
    params = {
        "query": f"{city_name} 맛집",
        "category_group_code": "FD6",  # 음식점(FD6) 고유 카테고리 필터
        "size": size,                  # 도시별 5곳 확보
        "sort": "accuracy"             # 정확도순 정렬
    }

    # [Commit 8 / 오류 방어 3-3] 5초 타임아웃을 지정하여 네트워크 지연 크래시 방어
    response = requests.get(url, headers=headers, params=params, timeout=5)
    response.raise_for_status()
    data = response.json()

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │ [Commit 8 / 오류 방어 3-1] 검색 결과 0건 ("데이터 없음") 방어 처리         │
    # │ 카카오 응답에 'documents'가 비어있는 경우 빈 리스트([])를 즉시 반환       │
    # └────────────────────────────────────────────────────────────────────────┘
    documents = data.get("documents", [])
    if not documents:
        return []

    restaurants = []
    for doc in documents:
        # [Commit 7] 필수 장소 필드 및 위경도 좌표(lat/lng) 명시적 추출
        restaurants.append({
            "place_name": doc.get("place_name", ""),
            "category_name": doc.get("category_name", ""),
            "phone": doc.get("phone", ""),
            "address": doc.get("address_name", ""),
            "road_address": doc.get("road_address_name", ""),
            "lat": doc.get("y", ""),                    # 위도 (Latitude / y)
            "lng": doc.get("x", ""),                    # 경도 (Longitude / x)
            "url": doc.get("place_url", "")             # 상세 장소 URL
        })

    return restaurants


def search_restaurants_for_cities(curation_data: dict, kakao_api_key: str, errors: list) -> list[dict]:
    """
    [Commit 7] 1차 추천된 다중 도시 목록을 순회하며 카카오 맛집 검색을 수행합니다. (도시별 5곳)
    [Commit 8 / 오류 방어 3] 에러 발생 시 프로그램을 중단하지 않고 비차단(Non-blocking)으로 격리합니다.
    """
    print(f" {Style.BURNT_ORANGE}[2/3] 추천 지역별 kakao API 로컬 맛집 검색 중...{Style.RESET}")
    restaurants_by_city = []

    cities = curation_data.get("recommended_cities", [])
    for city in cities:
        city_name = city.get("city_name", "")
        if not city_name:
            continue

        try:
            place_list = fetch_kakao_restaurants_by_city(city_name, kakao_api_key, size=5)

            # ┌────────────────────────────────────────────────────────────────┐
            # │ [Commit 8 / 오류 방어 3-1] 검색 결과 0건 ("데이터 없음") 상태 격리 │
            # └────────────────────────────────────────────────────────────────┘
            if len(place_list) == 0:
                restaurants_by_city.append({
                    "city_name": city_name,
                    "restaurant_count": 0,
                    "places": [],
                    "status": "NO_DATA"
                })
                print(f"   {Style.CONCRETE}ℹ [{city_name}] 등록된 맛집 데이터 없음 (0건){Style.RESET}")
            else:
                # [Commit 7] 정상 조회 성공 적재
                restaurants_by_city.append({
                    "city_name": city_name,
                    "restaurant_count": len(place_list),
                    "places": place_list,
                    "status": "SUCCESS"
                })
                print(f"   {Style.FOREST_GRN}✔ [{city_name}]{Style.RESET} 카카오 맛집 {len(place_list)}곳 조회 완료")

        # ┌────────────────────────────────────────────────────────────────────┐
        # │ [Commit 8 / 오류 방어 3-2] HTTP 401/403 인증 권한 에러 비차단 격리   │
        # └────────────────────────────────────────────────────────────────────┘
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response is not None else "UNKNOWN"
            errors.append({"step": "kakao_search", "type": f"HTTP_{status_code}_ERROR", "message": f"{city_name}: {str(http_err)}"})
            print(f"   {Style.BG_WARN} ⚠️ AUTH WARN {Style.RESET} {Style.BOLD}{Style.WHITE}[{city_name}]{Style.RESET} {Style.CONCRETE}카카오 인증/권한 오류 ({status_code}) - 건너뜁니다.{Style.RESET}")
            restaurants_by_city.append({"city_name": city_name, "restaurant_count": 0, "places": [], "status": f"HTTP_{status_code}_ERROR"})

        # ┌────────────────────────────────────────────────────────────────────┐
        # │ [Commit 8 / 오류 방어 3-3] 네트워크 타임아웃/접속 지연 비차단 격리 │
        # └────────────────────────────────────────────────────────────────────┘
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as conn_err:
            errors.append({"step": "kakao_search", "type": "NETWORK_TIMEOUT_OR_CONN_ERROR", "message": f"{city_name}: {str(conn_err)}"})
            print(f"   {Style.BG_WARN} ⚠️ NET WARN {Style.RESET} {Style.BOLD}{Style.WHITE}[{city_name}]{Style.RESET} {Style.CONCRETE}통신 장애/타임아웃 발생 - 건너뜁니다.{Style.RESET}")
            restaurants_by_city.append({"city_name": city_name, "restaurant_count": 0, "places": [], "status": "NETWORK_ERROR"})

        # ┌────────────────────────────────────────────────────────────────────┐
        # │ [Commit 7 에서 연장/ 오류 방어 3-4] 기타 모든 예외 격리 최종 안전망 │
        # └────────────────────────────────────────────────────────────────────┘
        except Exception as e:
            errors.append({"step": "kakao_search", "type": "SEARCH_EXCEPTION", "message": f"{city_name}: {str(e)}"})
            err_summary = "카카오 API 키/권한 오류" if "403" in str(e) or "401" in str(e) else str(e)
            print(f"   {Style.BG_WARN} ⚠️ KAKAO WARN {Style.RESET} {Style.BOLD}{Style.WHITE}[{city_name}]{Style.RESET} {Style.CONCRETE}맛집 검색 예외 발생 - 건너뜁니다 ({err_summary}){Style.RESET}")
            restaurants_by_city.append({"city_name": city_name, "restaurant_count": 0, "places": [], "status": "ERROR"})

    return restaurants_by_city


# ==============================================================================
# [Commit 9] Gemini 2차 종합 마크다운 리포트 생성 및 에러 요약 파이프라인
# ==============================================================================
def build_final_report_user_prompt(date_str: str, curation_data: dict, restaurant_data: list, errors: list) -> str:
    """
    [Commit 9] 1차 건축 큐레이션 결과와 2차 카카오 실시간 맛집 데이터, 시스템 에러 로그를
    결합하여 최종 마크다운 리포트 생성을 위한 User Prompt를 구성합니다.
    """
    season_key = get_season_key(date_str)
    theme_text, _ = get_seasonal_theme(date_str)

    user_prompt = f"""
[여행 기본 정보]
- 여행 일자: {date_str} ({season_key}철)
- 계절 테마: {theme_text}

# ┌────────────────────────────────────────────────────────────────────────┐
# │ [LLM 주입 데이터: 1차 추천 + 맛집 + 에러 로그 결합 컨텍스트]           │
# └────────────────────────────────────────────────────────────────────────┘
[1차 추천 명소 데이터 (JSON)]
{json.dumps(curation_data, ensure_ascii=False, indent=2)}

[카카오 로컬 실시간 맛집 데이터 (JSON)]
{json.dumps(restaurant_data, ensure_ascii=False, indent=2)}

[시스템 에러 로그 (JSON)]
{json.dumps(errors, ensure_ascii=False, indent=2)}

[마크다운 리포트 작성 가이드라인]
1. **리포트 제목**: 사유의 미학을 담은 서정적이고 품격 있는 메인 제목 (#)
2. **계절 테마 및 서문**: 해당 계절에 떠나는 사유와 건축 여행의 철학적 의미 소개
3. **추천 도시별 1일 사유 여행 코스 (추천된 각 도시마다 ## 로 개별 구성)**:
   - **명소 및 거장 소개**: 대표 사유 명소(main_attraction), 참여 건축가/조경가(master_designer), 공간 철학과 계절 날씨/정취
   
   # ┌────────────────────────────────────────────────────────────────────────┐
   # │ ✍️[추천 고도화] Gemini 2차 추론: 카카오 맛집 5곳 중 최적 1곳 최종 엄선  │
   # └────────────────────────────────────────────────────────────────────────┘
   - **🌿 도슨트 큐레이션 미식 가이드 (In-House Dining & Gemini Pick 1)**:
     * **[원내(院內) 품격 다이닝 강조]**: 만약 해당 명소가 '사유원'인 경우, 사유원 내부(원내)에 위치하여 자연과 노출 콘크리트 건축을 조망하며 식사할 수 있는 품격 있는 식음 공간(예: 사담, 몽몽마방 등 원내 다이닝/카페)에서 사유의 흐름을 끊지 않고 미식을 즐길 수 있다는 독보적인 장점을 매력적으로 어필하세요.
     * **[카카오 로컬 5곳 중 Gemini 최종 엄선 1곳]**: 제공된 [카카오 로컬 실시간 맛집 데이터] 5곳 중 사유 여행의 정취와 가장 어울리는 **'가장 정갈한 식당 단 1곳'을 LLM인 당신이 직접 2차 최종 엄선**하세요. 엄선된 식당의 상호명, 주소, 상세 링크 URL([상호명](url))을 명시하고 선정 이유를 2문장 내외로 서술하세요. (원내 식사 대안 또는 원외 방문용)
   
   # ┌────────────────────────────────────────────────────────────────────────┐
   # │ ✍️[추천 고도화] 엄선된 맛집을 1일 일정(점심)에 직접 매핑              │
   # └────────────────────────────────────────────────────────────────────────┘
   - **사색과 관조의 1일 동선 (Morning / Lunch / Afternoon / Evening)**:
     * **오전 (Morning)**: 자연 원형 속 거장의 건축물을 고요히 마주하는 사색의 시간
     * **점심 (Lunch)**: (사유원의 경우) 원내 다이닝 또는 위에서 **Gemini가 2차 엄선한 [식당명](URL)**에서의 정갈한 오찬
     * **오후 (Afternoon)**: 정원 및 주요 조경/전시 포인트 심층 탐방 (events 포인트 적극 반영)
     * **저녁 (Evening)**: 노을과 함께 하루의 여운을 정리하는 고즈넉한 마무리
   - **카카오 로컬 맛집 후보군 전체 목록 (5곳)**: 카카오가 검색해 온 5곳의 식당 후보 전체 정보를 불릿 기호로 깔끔하게 정리 (상호명, 주소, [상세보기 링크](url))
4. **여행자를 위한 사유 가이드 & 팁**: 이동 시 마음가짐, 복장, 관람 및 식음 시설 사전 예약 팁
5. **시스템 실행 상태 및 에러 요약 (Error Summary) (최하단 ##)**:
   - [시스템 에러 로그]를 분석하여 에러가 없으면 "모든 파이프라인이 결함 없이 정상 수행되었습니다." 기록
   - 에러가 존재할 경우 발생 단계(step), 유형(type), 사유(message)를 불릿 기호로 정리하여 투명하게 기록

오직 가독성이 뛰어난 순수 마크다운(Markdown) 텍스트로만 출력하세요.
"""
    return user_prompt


def generate_final_curation_report(
    date_str: str, 
    curation_data: dict,
    restaurant_data: list,
    errors: list,
    api_key: str
) -> str:
    """
    [Commit 9] Gemini 모델을 호출하여 최종 종합 마크다운 리포트를 생성합니다.
    """
    print(f" {Style.BURNT_ORANGE}[3/3] 여행 최종 마크다운 종합 리포트 생성 중 (LLM 2차 추론)...{Style.RESET}")
    client = genai.Client(api_key=api_key)

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │ 📜 [System Prompt] - 마크다운 작성을 위한 수석 도슨트 서술 페르소나  │
    # └────────────────────────────────────────────────────────────────────────┘
    system_prompt = (
        "당신은 '자연 원형과 거장의 건축 미학'을 깊이 있게 안내하는 국내 최고 권위의 '사유(思惟) 여행 수석 도슨트'입니다. "
        "제공된 명소, 맛집, 시스템 로그를 바탕으로 여행자에게 깊은 울림을 주는 품격 있는 마크다운 리포트를 작성합니다."
    )

    # 최종 리포트의 정갈하고 안정적인 서술을 위한 최적 온도 설정 (온도 0.7, top_p 0.9)
    config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.9,
        system_instruction=system_prompt,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    user_prompt = build_final_report_user_prompt(date_str, curation_data, restaurant_data, errors)

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_prompt,
            config=config
        )
        print(f"   {Style.SUCCESS_GRN}✔ 최종 종합 리포트 생성 완료{Style.RESET}\n")
        return response.text
    except Exception as e:
        errors.append({"step": "final_report_generation", "type": "REPORT_GEN_FAIL", "message": str(e)})
        print(f"\n{Style.BG_RED} ❌ REPORT ERROR {Style.RESET} {Style.BOLD}{Style.ORANGE}최종 리포트 생성 중 오류 발생: {e}{Style.RESET}")
        return (
            f"# [사유 여행 리포트 생성 실패]\n\n"
            f"리포트 생성 중 통신 오류가 발생하였습니다. ({e})\n\n"
            f"## 수집된 데이터 요약\n"
            f"- 여행 일자: {date_str}\n"
            f"- 추천 도시 수: {len(curation_data.get('recommended_cities', []))}\n"
        )


# ==============================================================================
# ┌────────────────────────────────────────────────────────────────────────────┐
# │ [Commit 10 / 보너스 2] 듀얼 파일 내보내기 & 0-Token 결과 캐싱 메커니즘        │
# │ - 원본 데이터 JSON (1차 큐레이션 + 카카오 맛집 + errors) 저장               │
# │ - 최종 마크다운 리포트 (.md) 영구 저장                                      │
# │ - 동일 날짜 재실행 시 외부 API 통신 전면 차단 (Zero-Token Cache Hit)        │
# └────────────────────────────────────────────────────────────────────────────┘
# ==============================================================================
RESULTS_DIR = "results"


def get_cache_file_paths(date_str: str) -> tuple[str, str]:
    """
    [Commit 10] 여행 날짜 기준 JSON 원본 캐시 파일 및 MD 리포트 파일 경로를 생성합니다.
    """
    json_path = os.path.join(RESULTS_DIR, f"travel_plan_{date_str}.json")
    md_path = os.path.join(RESULTS_DIR, f"travel_report_{date_str}.md")
    return json_path, md_path


def load_cached_results(date_str: str) -> tuple[dict | None, str | None]:
    """
    [Commit 10 / 보너스 2: 0-Token 캐싱 메커니즘]
    동일한 날짜(--date)로 실행 시, 이미 저장된 파일이 존재하면 디스크에서 즉시 로드합니다.
    외부 API(Gemini LLM 및 Kakao API) 호출을 100% 생략하여 비용과 토큰 소모를 제로(0)로 만듭니다.
    """
    json_path, md_path = get_cache_file_paths(date_str)

    if os.path.exists(json_path) and os.path.exists(md_path):
        try:
            with open(json_path, "r", encoding="utf-8") as jf:
                cached_json = json.load(jf)
            with open(md_path, "r", encoding="utf-8") as mf:
                cached_md = mf.read()
            return cached_json, cached_md
        except Exception:
            return None, None

    return None, None


def save_dual_results(date_str: str, raw_payload: dict, report_markdown: str):
    """
    [Commit 10 / 보너스 2: 듀얼 파일 내보내기]
    results/ 디렉터리를 자동 생성하고 원본 JSON 및 최종 Markdown 리포트를 파일로 영구 저장합니다.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    json_path, md_path = get_cache_file_paths(date_str)

    # 1. 원본 데이터 종합 JSON 저장 (1차 추천 + 맛집 검색 결과 + 에러 요약)
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(raw_payload, jf, ensure_ascii=False, indent=2)

    # 2. 최종 리포트 마크다운 (.md) 저장
    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(report_markdown)

    print(f"\n{Style.DARK_GRAY}──────────────────────────────────────────────────────────────────{Style.RESET}")
    print(f"{Style.SUCCESS_GRN} [Commit 10 / 듀얼 파일 저장 완료]{Style.RESET}")
    print(f"   {Style.FOREST_GRN}├─ 💾 원본 데이터 JSON :{Style.RESET} {Style.WHITE}{json_path}{Style.RESET}")
    print(f"   {Style.FOREST_GRN}└─ 📝 최종 리포트 MD   :{Style.RESET} {Style.WHITE}{md_path}{Style.RESET}")
    print(f"{Style.DARK_GRAY}──────────────────────────────────────────────────────────────────{Style.RESET}\n")


# ==============================================================================
# [Main Pipeline] CLI 실행 엔트리포인트 (0-Token 캐싱 분기 포함)
# ==============================================================================
def main():
    errors = []  # 시스템 전역 에러 격리 리스트

    args = parse_arguments()
    travel_date = validate_date(args.date)
    print_banner(travel_date)

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │ ⚡ [Commit 10 / 보너스 2] 0-Token 캐시 적중 검사 (Zero-Token Cache Hit)  │
    # │ 동일한 날짜의 캐시 파일이 존재하면 외부 API(Gemini/Kakao) 통신을 전면     │
    # │ 생략하고 디스크에서 리포트를 즉시 출력하여 토큰 소모를 0으로 만듭니다.    │
    # └────────────────────────────────────────────────────────────────────────┘
    cached_payload, cached_report = load_cached_results(travel_date)

    if cached_payload is not None and cached_report is not None:
        print(f"{Style.BG_CACHE} ⚡ ZERO-TOKEN CACHE HIT {Style.RESET} {Style.BOLD}{Style.SPRING_GRN}동일 날짜 캐시가 발견되어 모든 외부 API 호출을 생략합니다.{Style.RESET}")
        print(f"   {Style.CONCRETE}Token 소모량 :{Style.RESET} {Style.BOLD}{Style.WHITE}0 Tokens (비용 0원 최적화 달성){Style.RESET}")
        print(f"   {Style.CONCRETE}캐시 로드 경로 :{Style.RESET} {Style.DIM}results/travel_plan_{travel_date}.json / travel_report_{travel_date}.md{Style.RESET}\n")

       # 👈 캐시된 마크다운 리포트 즉시 출력 후 프로그램 종료 (API 호출 0회)       
        print(f"{Style.DARK_GRAY}══════════════════════════════════════════════════════════════════{Style.RESET}")
        print(cached_report)
        print(f"{Style.DARK_GRAY}══════════════════════════════════════════════════════════════════{Style.RESET}\n")
        return  # 👈 중요: 아래의 API 호출 코드들로 내려가지 않고 즉시 종료!

    # [Cache Miss] 캐시가 없을 때만 API 키 확인 및 전체 파이프라인 수행
    gemini_key, kakao_key = check_api_keys()

    # [Commit 5/6] 1차 추천 딕셔너리 획득
    curation_result = get_curated_recommendations_with_retry(travel_date, gemini_key, errors)

    # [Commit 7/8 / 오류 방어 3] 카카오 맛집 검색 및 예외 비차단 격리 파이프라인
    restaurant_results = search_restaurants_for_cities(curation_result, kakao_key, errors)

    # [Commit 9] 1차 추천 + 2차 맛집 + 에러 로그 결합 최종 마크다운 리포트 생성
    final_report_markdown = generate_final_curation_report(
        travel_date,
        curation_result,
        restaurant_results,
        errors,
        gemini_key
    )

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │ 💾[Commit 10 / 보너스 2] 원본 데이터 JSON 페이로드 구조화 및 듀얼 파일 저장│
    # └────────────────────────────────────────────────────────────────────────┘
    raw_payload = {
        "travel_date": travel_date,
        "created_at": datetime.now().isoformat(),
        "curation_result": curation_result,      # 1차 추천 JSON (파싱 결과)
        "restaurant_results": restaurant_results, # 맛집 검색 결과 (리스트, 0건 가능)
        "errors": errors                          # 오류 요약 (errors: array)
    }

    # 파일 영구 저장 실행 (results/ 폴더 자동 생성)
    save_dual_results(travel_date, raw_payload, final_report_markdown)

    # 최종 완성된 마크다운 리포트 콘솔 출력
    print(f"{Style.DARK_GRAY}══════════════════════════════════════════════════════════════════{Style.RESET}")
    print(final_report_markdown)
    print(f"{Style.DARK_GRAY}══════════════════════════════════════════════════════════════════{Style.RESET}\n")


if __name__ == "__main__":
    main()