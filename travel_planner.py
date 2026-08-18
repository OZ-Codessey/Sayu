# ==============================================================================
# [Imports & Dependencies] 필수 라이브러리 및 커밋별 사용 내역
# ==============================================================================
import argparse                 # [Commit 3] CLI 인자(--date) 파싱 및 표준 도움말 지원
import json                     # [Commit 5] Few-shot 예시 동적 직렬화 지원
import os                       # [Commit 4] 시스템 환경변수(API 키) 조회
import sys                      # [Commit 3] 유효성 검증 실패 시 예외 종료 (sys.exit)
from datetime import datetime   # [Commit 3] 날짜 유효성 검증 및 계절 테마 판별
from dotenv import load_dotenv  # [Commit 4] .env 파일 환경변수 로드

# [Commit 5 본격 연동] 최신 Google GenAI SDK
from google import genai
from google.genai import types


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
# [Commit 5 / 보너스 1] Gemini 1차 복수 여행지 추천 (테마의 장소 1 국한 주입)
# ==============================================================================
def call_gemini_multi_city_recommendation(date_str: str, api_key: str) -> str:
    """
    [Commit 5 / 보너스 1] 대중 관광지 배제 및 국내외 거장 사유 명소 2곳 엄선 (master_designer 필수)
    """
    client = genai.Client(api_key=api_key)

    season_key = get_season_key(date_str)
    theme_text, _ = get_seasonal_theme(date_str)

    system_instruction = (
        "당신은 인파로 붐비는 대중 상업 유흥 관광지를 철저히 배제하고, "
        "'보존된 자연 원형'과 '국내외 거장의 건축·조경·예술'이 융합된 침묵과 사색의 공간만을 큐레이션하는 '사유(思惟) 건축 전문 큐레이터'입니다.\n\n"
        "[추천 배제 기준]\n"
        "- 부산(해운대/광안리), 강릉(경포대), 제주도 전역, 속초, 여수 등 전형적인 상업 유흥 밀집지는 일절 배제합니다.\n\n"
        "[추천 필수 원칙]\n"
        "1. 승효상, 알바로 시자, 안도 타다오, 제임스 터렐, 김수근, 이타미 준, 정영선(조경가), 마리오 보타, 페터 춤토르, 민현식, 우규승 등 "
        "'실제 국내외 거장 건축가·조경가·공간예술가가 설계/참여하여 자연과 조화를 이루는 고유한 사유 공간'만 엄선합니다.\n"
        "2. [장소 1 (필수 시그니처)]: 대구 군위의 '사유원'을 1곳으로 포함하며, 제공된 사유원 전용 계절 테마를 반영하여 작성하세요.\n"
        "3. [장소 2 (계절 자율 큐레이션)]: 사유원 외 나머지 1곳은 사유원 테마에 종속되지 않고, 육지 전역(파주, 화성, 원주, 서울, 아산, 안양, 담양 등)의 다양한 거장 사유 명소 중 이번 계절에 어울리는 최적의 1곳을 자율적으로 엄선하세요.\n"
        "4. JSON 스키마의 'master_designer'(설계/참여 거장 및 핵심 영역) 필드를 반드시 명시하고, 오직 순수한 JSON 문자열만 반환하세요."
    )

    config = types.GenerateContentConfig(
        temperature=0.85,
        top_p=0.95,
        response_mime_type="application/json",
        system_instruction=system_instruction,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    dynamic_few_shot = {
        "recommended_cities": [
            {
                "city_name": "군위",
                "main_attraction": "사유원",
                "master_designer": "승효상(현암/사담), 알바로 시자(소요헌), 정영선(조경)",
                "weather": f"{season_key}철 기후 특징 요약",
                "events": ["사유 공간 산책 포인트 1", "사유 공간 산책 포인트 2"],
                "reason": "사유원의 계절 테마와 거장의 건축물이 전하는 고요한 사유의 가치를 2~3문장으로 서술합니다."
            },
            {
                "city_name": "선정된 지역명",
                "main_attraction": "선정된 거장 사유 공간명",
                "master_designer": "설계 거장 이름 및 핵심 영역 (예: 마리오 보타 - 건축)",
                "weather": "선정된 지역의 날씨 요약",
                "events": ["거장 건축 공간 사유", "자연 원형 정원 산책"],
                "reason": "해당 공간의 건축 철학과 자연이 선사하는 사유의 가치를 2~3문장으로 서술합니다."
            }
        ]
    }

    prompt = f"""
[여행 정보]
- 여행 일자: {date_str} ({season_key}철)

[요청 사항]
대중적 유흥지와 제주도를 배제하고, 자연 원형과 거장의 건축 미학이 살아 숨쉬는 국내 사유 명소 2곳을 선정하여 아래 JSON 형식으로 반환하세요.

1. [장소 1 (시그니처 고정)]
   - 대상: 군위 사유원
   - 계절 공간 테마: {theme_text} (이 테마는 오직 사유원의 공간 설명에만 반영하세요)

2. [장소 2 (전국 거장 사유 명소 자율 엄선)]
   - 대상: 군위 외 육지 전역(파주, 화성, 원주, 서울, 아산, 안양, 담양 등)에 위치한 거장 사유 공간 1곳
   - 조건: 사유원의 테마와 무관하게, 이번 {season_key}철 날씨와 어울리는 전국의 거장 명소를 자유롭고 다채롭게 선정하세요.

[JSON 형식 참고]
{json.dumps(dynamic_few_shot, ensure_ascii=False, indent=2)}
"""
    print(f" {Style.BURNT_ORANGE}[1/3] 1차 사유 여행지 추천 생성 중...{Style.RESET}")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=config
    )
    return response.text


# ==============================================================================
# [Main Pipeline] CLI 실행 엔트리포인트
# ==============================================================================
def main():
    args = parse_arguments()
    travel_date = validate_date(args.date)
    print_banner(travel_date)
    gemini_key, kakao_key = check_api_keys()
    raw_llm_response = call_gemini_multi_city_recommendation(travel_date, gemini_key)

    print(f"\n{Style.SUCCESS_GRN}✔ [1차 사유지 추천 완료]{Style.RESET}")
    print(f"{Style.DARK_GRAY}──────────────────────────────────────────────────────────────────{Style.RESET}")
    print(f"{raw_llm_response.strip()}")
    print(f"{Style.DARK_GRAY}──────────────────────────────────────────────────────────────────{Style.RESET}\n")


if __name__ == "__main__":
    main()