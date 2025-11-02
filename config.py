"""
티켓츠 QR 발권 시스템 - 설정 파일
"""

# QR 코드 유효 시간 (시간 단위)
QR_VALID_HOURS = 4

# SMS 인증 설정
SMS_CONFIG = {
    "code_length": 4,           # 인증번호 자릿수
    "valid_minutes": 3,         # 유효 시간 (분)
    "max_attempts": 5,          # 최대 시도 횟수
    "resend_cooldown": 30,      # 재발송 대기 시간 (초)
}

# 좌석 배치 설정 (공연별)
SEAT_LAYOUT = {
    "뮤지컬 오페라의 유령": {
        "sections": [
            {
                "name": "A구역 (VIP)",
                "rows": ["A"],
                "seats_per_row": 20,
                "color": "#2196F3",
                "price": 150000
            },
            {
                "name": "B구역 (R석)",
                "rows": ["B"],
                "seats_per_row": 15,
                "color": "#4CAF50",
                "price": 120000
            },
            {
                "name": "C구역 (S석)",
                "rows": ["C", "D"],
                "seats_per_row": 20,
                "color": "#FF9800",
                "price": 90000
            }
        ]
    },
    "콘서트 BTS": {
        "sections": [
            {
                "name": "스탠딩 A구역",
                "rows": ["A"],
                "seats_per_row": 30,
                "color": "#2196F3",
                "price": 200000
            },
            {
                "name": "스탠딩 B구역",
                "rows": ["B"],
                "seats_per_row": 30,
                "color": "#4CAF50",
                "price": 150000
            }
        ]
    },
    "연극 햄릿": {
        "sections": [
            {
                "name": "A구역",
                "rows": ["A"],
                "seats_per_row": 10,
                "color": "#2196F3",
                "price": 80000
            },
            {
                "name": "B구역",
                "rows": ["B", "C"],
                "seats_per_row": 15,
                "color": "#4CAF50",
                "price": 60000
            },
            {
                "name": "D구역",
                "rows": ["D"],
                "seats_per_row": 20,
                "color": "#FF9800",
                "price": 40000
            }
        ]
    }
}

# TCATS 브랜드 컬러
COLORS = {
    "primary": "#E31C25",      # 빨간색 (메인)
    "secondary": "#2196F3",    # 파란색 (좌석)
    "success": "#4CAF50",      # 녹색 (구역)
    "warning": "#FF9800",      # 주황색 (선택)
    "background": "#F5F5F5",   # 배경
    "text": "#333333"          # 텍스트
}

# 지역 목록 (읍면동)
REGIONS = [
    "서울 강남구",
    "서울 강동구",
    "서울 강북구",
    "서울 강서구",
    "서울 관악구",
    "서울 광진구",
    "서울 구로구",
    "서울 금천구",
    "서울 노원구",
    "서울 도봉구",
    "서울 동대문구",
    "서울 동작구",
    "서울 마포구",
    "서울 서대문구",
    "서울 서초구",
    "서울 성동구",
    "서울 성북구",
    "서울 송파구",
    "서울 양천구",
    "서울 영등포구",
    "서울 용산구",
    "서울 은평구",
    "서울 종로구",
    "서울 중구",
    "서울 중랑구",
    "부산 해운대구",
    "부산 수영구",
    "대구 중구",
    "인천 남동구",
    "광주 동구",
    "대전 유성구",
    "울산 남구",
    "세종시",
    "경기 수원시",
    "경기 성남시",
    "경기 고양시",
    "경기 용인시",
    "경기 부천시",
    "경기 안산시",
    "경기 남양주시",
    "경기 화성시",
    "경기 평택시",
    "기타"
]

# 스탬프북 혜택 목록
STAMP_BENEFITS = [
    {
        "name": "카페 아메리카노 50% 할인",
        "description": "지정 카페에서 아메리카노 50% 할인",
        "location": "공연장 주변 5km 이내",
        "valid_days": 30
    },
    {
        "name": "식당 10% 할인",
        "description": "제휴 식당 전 메뉴 10% 할인",
        "location": "공연장 주변 3km 이내",
        "valid_days": 30
    },
    {
        "name": "주차 1시간 무료",
        "description": "공연장 주차장 1시간 무료 이용",
        "location": "공연장 주차장",
        "valid_days": 30
    }
]
