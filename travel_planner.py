# ==============================================================================
# [Imports & Dependencies] 필수 라이브러리 및 커밋별 사용 내역
# ==============================================================================
import argparse                 # [Commit 3] CLI 인자(--date) 파싱 및 표준 도움말 지원
import json                     # [Commit 5/6] 템플릿 직렬화 및 LLM 응답 JSON 파싱/스키마 검증
import os                       # [Commit 4] 시스템 환경변수(API 키) 조회
import sys                      # [Commit 3] 유효성 검증 실패 시 예외 종료 (sys.exit)
from datetime import datetime   # [Commit 3] 날짜 유효성 검증 및 계절 테마 판별
from dotenv import load_dotenv  # [Commit 4] .env 파일 환경변수 로드

# [Commit 5] Google GenAI SDK
from google import genai
from google.genai import types
from google.genai.errors import APIError  # [Commit 6] LLM 통신/서버 에러 방어용

# [Commit 7] 카카오 로컬 REST API 통신용 라이브러리 (pip install requests)
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
# [Commit 5 / Commit 6] Gemini 1차 복수 추천 호출 및 재시도 프롬프트
# ==============================================================================
def build_curation_prompt(date_str: str, is_retry: bool = False) -> str:
    """
    [Commit 5/6] 1차 여행지 추천용 프롬프트 (스켈레톤 구조 템플릿 적용, 2~3곳 가변 큐레이션)
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

    prompt = f"""
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
    return prompt


def call_gemini_multi_city_recommendation(date_str: str, api_key: str, is_retry: bool = False) -> str:
    """
    [Commit 5/6] Gemini LLM 1차 여행지 추천 호출 함수
    """
    client = genai.Client(api_key=api_key)

    system_instruction = (
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

    config = types.GenerateContentConfig(
        temperature=0.85,
        top_p=0.95,
        response_mime_type="application/json",
        system_instruction=system_instruction,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    prompt = build_curation_prompt(date_str, is_retry=is_retry)
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
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
    print(f" {Style.BURNT_ORANGE}[1/3] 1차 여행지 추천 생성 중...{Style.RESET}")

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

    response = requests.get(url, headers=headers, params=params, timeout=5)
    response.raise_for_status()
    data = response.json()

    restaurants = []
    for doc in data.get("documents", []):
        # 🌟 [과제 공통 조건] 필수 장소 필드 및 위경도 좌표(lat/lng) 명시적 확보
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
    """
    print(f" {Style.BURNT_ORANGE}[2/3] 추천 지역별 카카오 로컬 맛집 검색 중...{Style.RESET}")
    restaurants_by_city = []

    cities = curation_data.get("recommended_cities", [])
    for city in cities:
        city_name = city.get("city_name", "")
        if not city_name:
            continue

        try:
            place_list = fetch_kakao_restaurants_by_city(city_name, kakao_api_key, size=5)
            restaurants_by_city.append({
                "city_name": city_name,
                "restaurant_count": len(place_list),
                "places": place_list
            })
            print(f"   {Style.FOREST_GRN}✔ [{city_name}]{Style.RESET} 카카오 맛집 {len(place_list)}곳 조회 완료")
        except Exception as e:
            errors.append({"step": "kakao_search", "type": "SEARCH_ERROR", "message": f"{city_name}: {str(e)}"})
            err_summary = "카카오 API 키/권한 오류" if "403" in str(e) or "401" in str(e) else str(e)
            print(f"   {Style.BG_WARN} ⚠️ KAKAO WARN {Style.RESET} {Style.BOLD}{Style.WHITE}[{city_name}]{Style.RESET} {Style.CONCRETE}맛집 검색 실패 ({err_summary}){Style.RESET}")

    return restaurants_by_city


# ==============================================================================
# [Main Pipeline] CLI 실행 엔트리포인트
# ==============================================================================
def main():
    errors = []  # 시스템 전역 에러 격리 리스트

    args = parse_arguments()
    travel_date = validate_date(args.date)
    print_banner(travel_date)
    gemini_key, kakao_key = check_api_keys()

    # [Commit 6] 파싱 및 스키마 검증이 완료된 1차 추천 딕셔너리 획득
    curation_result = get_curated_recommendations_with_retry(travel_date, gemini_key, errors)

    # [Commit 7] 카카오 다중 도시 맛집 검색 파이프라인 연동 (도시별 5곳, lat/lng 좌표 포함)
    restaurant_results = search_restaurants_for_cities(curation_result, kakao_key, errors)

    print(f"\n{Style.SUCCESS_GRN}✔ [카카오 맛집 검색 결과]{Style.RESET}")
    print(f"{Style.DARK_GRAY}──────────────────────────────────────────────────────────────────{Style.RESET}")
    print(json.dumps(restaurant_results, ensure_ascii=False, indent=2))
    print(f"{Style.DARK_GRAY}──────────────────────────────────────────────────────────────────{Style.RESET}\n")


if __name__ == "__main__":
    main()