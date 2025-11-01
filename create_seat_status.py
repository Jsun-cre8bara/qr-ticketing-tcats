import json
import os

# 좌석 현황 초기 데이터
# 실제로는 데이터베이스에서 관리해야 하지만, 간단히 JSON 파일로
seat_status = {
    "뮤지컬 오페라의 유령": {
        "2024-11-15": {
            "14:00": {
                "occupied": ["A-12", "A-13", "A-14", "B-05"],  # 이미 예약된 좌석
                "selected": []  # 현재 선택 중인 좌석
            },
            "19:00": {
                "occupied": ["B-05"],
                "selected": []
            }
        },
        "2024-11-16": {
            "14:00": {
                "occupied": [],
                "selected": []
            }
        }
    },
    "콘서트 BTS": {
        "2024-11-20": {
            "18:00": {
                "occupied": [],
                "selected": []
            }
        }
    },
    "연극 햄릿": {
        "2024-11-25": {
            "15:00": {
                "occupied": ["D-08"],
                "selected": []
            }
        }
    }
}

# data 폴더 생성
os.makedirs('data', exist_ok=True)

# JSON 파일로 저장
with open('data/seat_status.json', 'w', encoding='utf-8') as f:
    json.dump(seat_status, f, ensure_ascii=False, indent=2)

print("✅ 좌석 현황 파일이 생성되었습니다!")
print("📁 위치: data/seat_status.json")
