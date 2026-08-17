import argparse
import sys
from datetime import datetime

# ==============================================================================
# [Design System] 자연과 건축의 여정 (ANSI 색채 & 타이포그래피)
# ==============================================================================
class Style:
    RESET       = "\033[0m"
    BOLD        = "\033[1m"
    DIM         = "\033[2m"
    ITALIC      = "\033[3m"
    UNDERLINE   = "\033[4m"

    # [핵심 색채 시스템]
    ORANGE      = "\033[38;5;208m"  # 시그니처 코르텐 오렌지
    BURNT_ORANGE= "\033[38;5;166m"  # 짙은 탄주황 글자색
    YELLOW      = "\033[38;5;220m"  # 샛노란 빛 / 알림 강조
    FOREST_GRN  = "\033[38;5;35m"   # 수목원 솔숲 딥그린
    SPRING_GRN  = "\033[38;5;119m"  # 봄 새순 연둣빛
    WATER_BLUE  = "\033[38;5;74m"   # 사담 수면 블루
    CONCRETE    = "\033[38;5;246m"  # 노출 콘크리트 그레이
    DARK_GRAY   = "\033[38;5;240m"  # 구분선 및 보조 텍스트
    WHITE       = "\033[38;5;255m"  # 선명한 화이트
    SUCCESS_GRN = "\033[1m\033[38;5;71m"  # 작업 완료 진한 초록 볼드

    # [배경 음영 배지]
    BG_BURNT    = "\033[48;5;166m\033[38;5;232m\033[1m"  # 짙은 탄주황 음영 배지
    BG_WARN     = "\033[48;5;214m\033[38;5;232m\033[1m"  # 호박색 재시도 배지
    BG_RED      = "\033[48;5;196m\033[38;5;255m\033[1m"  # 적색 에러 배지


# ==============================================================================
# [Commit 3] CLI 인자 파싱, 날짜 유효성 검증 [오류 방어 1-1] 및 배너 출력
# ==============================================================================

def get_seasonal_theme(date_str: str) -> tuple[str, str]:
    """
    [Commit 3] 입력된 날짜(월)를 분석하여 사계절 공간 테마를 반환합니다.
    """
    try:
        month = datetime.strptime(date_str, "%Y-%m-%d").month
    except ValueError:
        month = 10

    if month in [3, 4, 5]:
        return "봄-시자의 하얀 목련", Style.ORANGE
    elif month in [6, 7, 8]:
        return "여름 별유동천-백일간의 붉음", Style.ORANGE
    elif month in [9, 10, 11]:
        return "가을 풍설기천년-천년의 모과빛", Style.ORANGE
    else:
        return "겨울-오래도록 홀로 푸르른 솔", Style.ORANGE


def print_banner(date_str: str):
    """
    [Commit 3] 상단 브랜딩 배너를 출력합니다.
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
    [Commit 3] CLI 명령줄 인자를 파싱합니다. (--date 필수 옵션)
    """
    parser = argparse.ArgumentParser(
        description="자연과 건축 기반 사유(思惟) 여행 큐레이션 CLI 도구",
        usage="python travel_planner.py --date \"YYYY-MM-DD\""
    )
    parser.add_argument(
        "--date", 
        type=str, 
        required=True, 
        help="여행 날짜 (YYYY-MM-DD 형식, 필수)"
    )
    return parser.parse_args()


# ==============================================================================
# [오류 방어 1-1] 잘못된 날짜 형식 및 미존재 날짜 방어 (예: 2026-13-45 등)
# ==============================================================================
def validate_date(date_str: str) -> str:
    """
    [Commit 3 / 오류 방어 1-1] 날짜 유효성 검증 및 포맷 오류 방어
    """
    date_format = "%Y-%m-%d"
    try:
        valid_date = datetime.strptime(date_str, date_format)
        return valid_date.strftime(date_format)
    except ValueError:
        print(f"\n{Style.BG_RED} ❌ INPUT ERROR {Style.RESET} {Style.BOLD}{Style.ORANGE}날짜 형식이 올바르지 않거나 존재하지 않는 날짜입니다.{Style.RESET}")
        print(f"   {Style.CONCRETE}입력값 : {date_str}{Style.RESET}")
        print(f"   {Style.ORANGE}💡 올바른 사용법: python travel_planner.py --date \"YYYY-MM-DD\" (예: 2026-10-25){Style.RESET}\n")
        sys.exit(1)


def main():
    # 1. 인자 파싱
    args = parse_arguments()
    
    # 2. 날짜 유효성 검증 [오류 방어 1-1]
    travel_date = validate_date(args.date)
    
    # 3. 배너 출력
    print_banner(travel_date)
    
    # 4. Commit 3 초기화 완료 안내
    print(f"{Style.SUCCESS_GRN}✔ [CLI 초기화] 파라미터 및 공간 테마 검증이 완료되었습니다.{Style.RESET}")
    print(f"  {Style.CONCRETE}파이프라인 준비 상태: 정상 (API 키 보안 검증 레이어로 진입 준비 완료){Style.RESET}\n")


if __name__ == "__main__":
    main()