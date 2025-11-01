"""
티켓츠 QR 발권 시스템 - 설정 파일
"""

# QR 코드 유효 시간 (시간 단위)
QR_VALID_HOURS = 4

# SMS 인증 설정
SMS_CONFIG = {
    "code_length": 4,
    "valid_minutes": 3,
    "max_attempts": 5,
    "resend_cooldown": 30,
}

# 좌석 배치 설정
SEAT_LAYOUT = {
    "뮤지컬 오페라의 유령": {
        "sections": {
            "A": {
                "name": "A구역 (VIP)",
                "rows": ["A"],
                "seats_per_row": 14,
                "color": "#2196F3",  # 파란색
                "price": 150000
            },
            "B": {
                "name": "B구역 (R석)",
                "rows": ["B"],
                "seats_per_row": 10,
                "color": "#4CAF50",  # 녹색
                "price": 120000
            },
            "C": {
                "name": "C구역 (S석)",
                "rows": ["C", "D"],
                "seats_per_row": 12,
                "color": "#FF9800",  # 주황색
                "price": 90000
            }
        }
    },
    "콘서트 BTS": {
        "sections": {
            "A": {
                "name": "스탠딩 A구역",
                "rows": ["A"],
                "seats_per_row": 20,
                "color": "#2196F3",
                "price": 200000
            },
            "B": {
                "name": "스탠딩 B구역",
                "rows": ["B"],
                "seats_per_row": 20,
                "color": "#4CAF50",
                "price": 150000
            }
        }
    },
    "연극 햄릿": {
        "sections": {
            "A": {
                "name": "A구역",
                "rows": ["A"],
                "seats_per_row": 8,
                "color": "#2196F3",
                "price": 80000
            },
            "B": {
                "name": "B구역",
                "rows": ["B", "C"],
                "seats_per_row": 10,
                "color": "#4CAF50",
                "price": 60000
            },
            "D": {
                "name": "D구역",
                "rows": ["D"],
                "seats_per_row": 12,
                "color": "#FF9800",
                "price": 40000
            }
        }
    }
}

# TCATS 브랜드 컬러
COLORS = {
    "primary": "#E31C25",
    "secondary": "#2196F3",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "background": "#F5F5F5",
    "text": "#333333",
    "seat_available": "#FFFFFF",    # 선택 가능
    "seat_selected": "#FFD700",     # 선택됨 (금색)
    "seat_occupied": "#999999",     # 예약됨 (회색)
}

# 지역 목록
REGIONS = [
    "서울 강남구", "서울 강동구", "서울 강북구", "서울 강서구",
    "서울 관악구", "서울 광진구", "서울 구로구", "서울 금천구",
    "서울 노원구", "서울 도봉구", "서울 동대문구", "서울 동작구",
    "서울 마포구", "서울 서대문구", "서울 서초구", "서울 성동구",
    "서울 성북구", "서울 송파구", "서울 양천구", "서울 영등포구",
    "서울 용산구", "서울 은평구", "서울 종로구", "서울 중구",
    "서울 중랑구", "기타"
]

# 스탬프북 혜택
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
