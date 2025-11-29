# QR 티켓 발급 및 검증 PRD (초안)

## 1. 배경 및 목표
- 공연/전시/일반 행사에서 **참가자 확인**을 위한 QR 티켓 발급 및 검증 시스템을 구축한다.
- **조회 기준**은 이름 + 전화번호이며, 전화번호는 11자리가 없는 경우 **뒤 4자리**만으로 매칭한다. DB 조회 시 와일드카드 매칭을 허용해 동일 이름·번호 조합이 있는지 확인한다.
- **QR에 포함**되는 최소 정보는 `티켓 ID`, `이름`, `좌석 정보`다.
- 발권 후 **20시간** 동안 유효하며, **재발행 가능**(이전 QR 무효화 + 사용자 인증 필요).
- 입장 시 관리자 휴대폰의 QR 리더로 스캔하고, 백엔드 응답 없이 **입장 현황 좌석배치도**에 기록한다. 필요 시 **오프라인 검증**도 지원한다.

## 2. 사용자 시나리오
1. 홍길동이 티켓 3매를 예매한다(예: DB에는 "홍길동" 3매로 기록).
2. 홍길동이 모바일/웹에서 QR 3장을 발급받는다.
3. 동행 2명에게 각 QR을 카톡/문자로 전달한다.
4. 동행이 QR을 수신할 때 **본인 정보(이름, 연락처, 성별)**를 입력해 소유권을 명시한다. 성별 입력은 **선택값(남성/여성)** 드롭다운으로 제한한다.
5. 행사장에서 관리자 휴대폰 리더로 QR을 스캔 → 좌석배치도에 입장 처리 기록.
6. 네트워크가 불안정한 경우 오프라인 검증 흐름으로 진위 여부 확인.

## 3. 정책 정리 (필수 반영)
- **조회 기준**: 이름 + 전화번호. 전화번호는 11자리가 아니면 뒤 4자리로 매칭, DB 조회 시 와일드카드를 허용해 동일 여부 확인.
- **QR 포맷 제안**:
  - QR에는 **짧은 URL**을 넣고, URL 쿼리/프래그먼트에 **서명된 토큰**을 포함한다. 토큰 페이로드: `ticket_id`, `owner_name`, `seat_info`, `issued_at`, `expires_at`, `nonce`.
  - 토큰은 **서명 + 만료 시간**을 포함하고, 재발행 시 이전 토큰을 블랙리스트/버전 관리로 무효화.
  - 동행자 전달 시 **소유자 정보 수집 폼**(이름/연락처/성별=선택값)을 URL 단계에서 노출해 본인 정보를 받아 토큰과 **소유자-이름/연락처 바인딩**을 수행.
- **유효 기간**: 발권 시점부터 20시간. 서버 검증 시 `expires_at` 확인 후 만료 처리.
- **재발행**: 허용. 재발행 시 이전 QR은 즉시 무효화하고 사용자 인증은 **SMS 1회용 코드**로 진행해 새 토큰을 발급한다.
- **검증 흐름**: 관리자 휴대폰 **전용 리더 앱** → (온라인) 백엔드 토큰 검증 및 좌석배치도 업데이트. 응답 메시지는 최소화(필요 시 리더 앱 내부에만 표시)하고 서버에는 **입장 기록(시간, 리더 ID, 좌석)**을 저장. 리더 앱 ↔ 백엔드 인증은 **OAuth2 Client Credentials**로 진행하며, 단말별 `client_id`/`client_secret`을 발급하고 **1시간 이하 Access Token**을 사용한다(향후 단말 권한/입장구역 권한 관리 확장 가능).
- **오프라인 검증**: 리더 앱에 **공개키 기반 서명 검증**(예: ECDSA 공개키 포함)과 **짧은 CRL/블랙리스트 캐시**를 제공한다. 블랙리스트/키 캐시는 관리자가 리더 앱(또는 관리자 페이지)에서 "동기화" 버튼을 눌렀을 때 최신 상태로 내려받는 **수동 동기화**를 기본으로 한다.
- **보안 권장사항**:
  - 토큰 서명(예: JWT/Compact JWS) 및 `nonce`로 재사용 방지.
  - 리더 앱 요청에 **속도 제한** 및 시도 실패 누적 시 운영자 알림. **입장 처리 속도 목표는 P95 300ms 이하, 최악 1초 이내**이며, 네트워크 지연 시 리더 앱이 재시도를 안내한다.
  - 민감 데이터(연락처) 저장 시 **암호화/마스킹**, 전송 구간 TLS 적용.
- **실패 메시지**: 사용자에게 "운영자에게 문의하세요"만 노출. 리더/운영자 화면에는 상세 오류 코드(만료/중복 사용/위조/재발행 무효)를 별도로 표시 가능.

## 4. 기능 요구사항
### 4.1 발급/재발행
- [ ] 이름+전화번호 기준으로 예약 검색 후 티켓 ID/좌석 정보 매칭.
- [ ] 발급 시 토큰 생성: `ticket_id`, `owner_name`, `seat_info`, `issued_at`, `expires_at = issued_at + 20h`, `nonce`, `version`.
- [ ] 재발행 시: 신규 토큰 발급, `version` 증가 또는 블랙리스트에 이전 토큰 등록. 사용자 인증은 **SMS 1회용 코드**.
- [ ] 동행 전달 흐름: 전달 링크에서 동행자의 **이름/연락처/성별(선택값)** 입력 폼 표시 후 토큰을 동행자 정보로 서명/바인딩.

### 4.2 검증/입장 처리
- [ ] **전용 리더 앱**에서 QR 스캔 → 토큰 서명/만료 검증.
- [ ] 리더 앱 ↔ 백엔드 통신은 **OAuth2 Client Credentials**로 인증(단말별 `client_id`/`client_secret`, Access Token 유효기간 ≤ 1h).
- [ ] 온라인 검증 응답 시간 목표: **P95 300ms 이하, 최악 1초 이내**. 네트워크 지연 시 리더 앱이 재시도를 안내.
- [ ] 검증 성공 시 좌석배치도에 **입장 기록** 저장(시간, 리더 ID, 좌석, 티켓 ID, 소유자 정보).
- [ ] 중복 사용/만료/위조 시 실패 처리 및 리더 화면에 원인 표시(사용자 화면은 공통 메시지).
- [ ] 오프라인 모드: 캐시된 공개키/블랙리스트로 서명 검증 후 결과 로컬 저장, 온라인 복귀 시 동기화. 블랙리스트는 리더/관리자 페이지에서 **동기화 버튼** 클릭 시 최신 상태로 갱신.

### 4.3 운영/관리
- [ ] 블랙리스트/버전 관리 테이블로 무효 토큰 관리.
- [ ] 리더 앱별 계정/디바이스 ID 관리, 동기화 로그 확인.
- [ ] 감사 로그: 발급/재발행/검증 이벤트 기록.
- [ ] 오프라인 검증용 공개키 **90일 주기 로테이션**, 필요 시 즉시 교체 + **7일 롤링 호환**을 지원.
- [ ] 블랙리스트/캐시 동기화 실패 시 리더 앱에 **경고 배너 + 즉시 재동기화 버튼**을 노출하고, 지속 실패 시 위험 안내.
- [ ] 감사 로그는 **180일 보존 후 자동 삭제**, CSV/JSON Export 제공.
- [ ] **좌석배치도/입장 기록 백엔드**를 이번 프로젝트에서 신규 설계 및 구축하며, **그래픽 좌석도 UI**(구역/열/좌석 배치)로 초기 제공.

## 5. 데이터 모델(제안)
- **tickets**: `id`, `performance_id`, `name`, `phone`, `seat_info`, `quantity`, `status`, `created_at`.
- **ticket_tokens**: `id`, `ticket_id`, `token_version`, `issued_at`, `expires_at`, `revoked_at`, `revoked_reason`, `nonce`.
- **entry_logs**: `id`, `ticket_id`, `seat_info`, `scanned_at`, `scanner_id`, `result`.
- **offline_cache_meta**: 공개키 버전, 블랙리스트 해시, 마지막 동기화 시각.

## 6. 결정된 추가 정책 (사용자 답변 반영)
- 성별 입력은 **선택값(남성/여성)**으로 제공한다.
- 사용자 인증은 **SMS 1회용 코드**로 진행한다.
- 리더는 **별도 모바일 앱**으로 개발한다.
- 오프라인 검증용 블랙리스트/키 캐시는 **관리자/리더 앱에서 "동기화" 버튼을 눌러 수동으로 최신화**한다(검증용 데이터 의미: 재발행으로 무효화된 토큰 목록, 최신 공개키 등).
- 좌석배치도/입장 기록을 저장하는 백엔드/DB는 **이번 프로젝트에서 신규 설계**하며, **그래픽 좌석도 UI**(구역/열/좌석 배치 기반)로 초기 버전부터 제공한다. 가격 구간 설정, 영역 잠금 등 운영 기능을 염두에 둔다.
- **API 응답 포맷(확정)**:
  - 발급/재발행 성공 시 JSON: `token`(서버 검증용 단문 토큰), `expires_at`(ISO8601), `seat_info`, 선택 필드 `issued_at`, `version`. `qr_image_url`은 필요 시 추후 협의해 추가한다.
  - 에러 시 HTTP status code + JSON 바디(`code`, `message`)로 통일한다.
- **SMS 발송 설계 방향**: 개발은 **추상 인터페이스 + 샘플(가짜/테스트) 구현체**로 진행하고, 실제 상용 공급자는 운영 준비 단계에서 확정한다.
- **오프라인 검증 키 관리**: 공개키는 **90일 주기로 로테이션**하며, 운영자가 필요 시 즉시 교체할 수 있어야 한다. 리더 앱은 **신/구 키를 모두 수용하는 7일 롤링 기간**을 지원한다.
- **블랙리스트/캐시 동기화 실패 UX**: 동기화 실패 시 스캔을 막지 않고 리더 앱에 **안전도 저하 경고 배너**를 노출한다.
  - 메시지 예시: "최근 N분 동안 서버와 동기화되지 않았습니다. 네트워크 상태 확인 후 재시도해 주세요." + **즉시 재동기화 버튼**.
  - 지속 실패 시: "캐싱 정보가 오래되었습니다. 재입장/환불 관련 오류가 발생할 수 있습니다. 운영자에게 확인해 주세요."
- **감사 로그 보존 정책**: 감사 로그는 **180일 보존 후 자동 삭제**하며, CSV/JSON Export 기능을 제공한다. 향후 고객사 요구에 따라 90일/180일/1년 선택 옵션을 검토한다.

## 7. 진행 체크리스트(주니어 개발자용)
- 한 번에 한 가지 Task만 진행하고, **각 Task 결과를 사용자에게 확인**받은 뒤 다음 Task로 넘어간다.
- 아래 체크박스는 진행 현황을 위한 것이며, 실제 업무 시작 전마다 "사용자 확인 질문"을 먼저 전달한다.

### 7.1 Task 목록
- [ ] T1. 발급/재발행 설계 및 API 계약서 초안 작성
- [ ] T2. 검증/입장 처리 설계 및 리더 앱-백엔드 인터페이스 정의
- [ ] T3. 오프라인 검증 및 동기화 로직 설계(공개키/블랙리스트 캐시 포함)
- [ ] T4. 운영/모니터링(블랙리스트 관리, 감사 로그, 좌석배치도 백엔드) 설계

### 7.2 Task별 사용자 확인/진행 상태(번호 목록)
**T1 시작 전**
1. ✅ 발급/재발행 API 응답 포맷은 **JSON**으로 확정: `token`, `expires_at`, `seat_info`(+ 선택 `issued_at`, `version`), 에러는 HTTP status + JSON(`code`, `message`).
2. ⚠️ SMS 발송 서비스는 **추상 인터페이스 + 샘플(가짜/테스트) 구현체**로 개발 후, **상용 공급자는 운영 준비 단계에서 확정** 예정입니다. 운영 단계에서 선호 공급자나 기존 게이트웨이가 있다면 알려주세요.

**T2 시작 전**
3. ✅ 리더 앱 ↔ 백엔드 인증은 **OAuth2 Client Credentials**로 진행(단말별 `client_id`/`client_secret`, 단기 Access Token 사용).
4. ✅ 입장 처리 속도 목표는 **P95 300ms 이하, 최악 1초 이내**. 네트워크 지연 시 리더 앱에서 재시도 안내.

**T3 시작 전**
5. ✅ 오프라인 검증용 공개키는 **90일 주기 로테이션**, 필요 시 즉시 교체 + **7일 롤링 호환**.
6. ✅ 블랙리스트/캐시 동기화 실패 시 **경고 배너 + 즉시 재동기화 버튼**, 지속 실패 시 위험 안내.

**T4 시작 전**
7. ✅ 관리자 페이지 좌석배치도는 초기부터 **그래픽 좌석도 UI**로 개발(구역/열/좌석 배치 반영).
8. ✅ 감사 로그 **180일 보존** 후 자동 삭제, Export(CSV/JSON) 제공. 향후 90/180/365일 선택 옵션 검토.

> 위 확인 상태를 기준으로 한 번에 한 Task만 "진행"으로 전환하고, 완료 후 사용자 확인을 받은 뒤 다음 Task로 이동한다.

## 8. 예약/좌석/QR 구현 요구사항(사용자 답변 반영)
주니어 개발자가 바로 착수할 수 있도록 DB 스키마, 상태 머신, API, UI 요구사항을 정리했다. 모든 항목은 **PostgreSQL + Raw SQL 마이그레이션 스크립트**를 기준으로 작성했으며, 다른 마이그레이션 도구를 쓰고 싶다면 사용자에게 먼저 확인한다.

### 8.1 DB 마이그레이션
- **reservations 테이블 컬럼 추가**
  - `token CHAR(8)` : Base36 8자리, 예약마다 고유. `UNIQUE` 제약 조건 권장.
  - `status reservations_status` : ENUM(`pending`, `reserved_unassigned`, `reserved_assigned`, `issued`, `checked_in`, `cancelled`, `expired`).
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
- **ENUM 생성**: `CREATE TYPE reservations_status AS ENUM (...)`.
- **updated_at 자동 갱신 트리거**: 모든 `UPDATE` 시 `NEW.updated_at = now()`를 강제하는 `BEFORE UPDATE` 트리거를 생성한다.
- **seat_status 테이블(초안)**
  - `id BIGSERIAL PRIMARY KEY`
  - `performance_id BIGINT NOT NULL` (좌석이 속한 회차)
  - `seat_code TEXT NOT NULL` (예: "A-10")
  - `reservation_id BIGINT NULL` (배정된 예약 ID, 없으면 NULL)
  - `status TEXT NOT NULL` (예: `available`, `held`, `reserved`, `checked_in` — 필요 시 사용자에게 확정 요청)
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- **reservation_events 테이블**
  - `id BIGSERIAL PRIMARY KEY`
  - `reservation_id BIGINT NOT NULL` (FK → reservations)
  - `event_type TEXT NOT NULL` (예: `status_transition`, `token_issued`, `token_revoked`)
  - `prev_status reservations_status NULL`
  - `new_status reservations_status NULL`
  - `actor_type TEXT NOT NULL` (예: `system`, `operator`, `user`)
  - `actor_id TEXT NULL` (연동 시스템 ID 또는 운영자 ID)
  - `metadata JSONB DEFAULT '{}'::JSONB`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- **인덱스**: `reservation_events(reservation_id, created_at DESC)`, `seat_status(performance_id, seat_code)` 권장.

### 8.2 상태 머신
- 기본 플로우: `pending → reserved_unassigned → reserved_assigned → issued → checked_in`.
- `cancelled`: 언제든 이동 가능(단, `checked_in` 이후 역전이 금지).
- `expired`: 회차 종료 배치 Job에서 일괄 처리.
- `checked_in` 이후에는 다른 상태로 전환하지 않는다.
- 상태 전환 시 `reservation_events`에 `prev_status`, `new_status`, `actor_type`, `actor_id`를 기록하고, `reservations.updated_at`은 트리거로 자동 갱신한다.

### 8.3 토큰 생성/발급
- 규칙: **Base36 8자리**, 중복 없는 고유값 생성 후 `reservations.token`에 저장.
- 발급 시점 옵션(사용자 답변):
  1) 예약 생성 시 즉시 발급
  2) 좌석 지정 후 발급
  3) 운영자가 "발급" 버튼 클릭 시 발급 **(추천)**
- 권장 로직: 옵션 3을 기본값으로 개발하고, 옵션 1/2는 구성 플래그로 전환 가능하게 설계.
- 토큰 생성 실패/중복 시 재시도 로직 포함, 발급 성공 시 `reservation_events`에 `token_issued` 기록.

### 8.4 API 요구사항
- **발급 API**: 내부 어드민 전용이라면 인증 생략 가능하나, 기본 가이드로 **JWT 또는 API Key** 헤더 인증을 권장.
  - 요청: `POST /api/reservations/{id}/issue-token` (또는 `/issue`), 필요 시 `force: true` 옵션.
  - 응답: `{ "reservation_id": ..., "token": "8자리", "status": "issued", "updated_at": "ISO8601" }`.
- **QR 생성 API**
  - QR 데이터: `{"r": <reservation_id>, "t": "<token>"}`
  - 포맷: PNG
  - 응답: `Content-Type: image/png` 바이너리 또는 `base64` JSON 둘 중 택 1. (기본: PNG 바이너리)
- **검증/체크인**: QR 스캔 → 토큰 검증 후 상태를 `checked_in`으로 업데이트, 이벤트 로그 기록.

### 8.5 좌석별 QR UI 요구사항
- 뷰 구조: 아코디언 **Zone → Row** 2단계 그룹.
- 각 좌석 카드: QR 이미지, 좌석코드, 상태 표시, **링크 복사**(QR 조회 링크), **PNG 다운로드** 버튼.
- 상태별 버튼 가이드: `issued` 이상만 QR/다운로드 노출, `pending/reserved*`은 발급 버튼 노출.

### 8.6 QA/테스트 기준
- **API smoke test**: 발급/검증 기본 흐름.
- **발급/검증 E2E test**: 생성 → 발급 → QR 생성 → 검증 → 체크인.
- **좌석 추천/예외 케이스**: 좌석 미지정 → 배정 → 발급 경로, 중복 발급 방지, 만료 처리.

### 8.7 사용자 확인 질문 리스트 (Task 시작 전)
아래 질문에 답변을 받으면 **T1부터 순차 진행**한다. 한 번에 한 Task만 실행.
1. ✅ DB는 **PostgreSQL** 사용이 맞나요? 마이그레이션을 **Raw SQL 스크립트**로 진행해도 될까요? (도구 변경 시 알려주세요)
2. ✅ `seat_status.status` 값은 `available/held/reserved/checked_in`으로 진행해도 될까요? 다른 상태가 필요하면 알려주세요.
3. ✅ QR 생성 API 응답을 **PNG 바이너리**로 기본 제공하고, `?format=base64` 옵션을 추가해도 될까요?
4. ✅ 발급 API 인증 방식을 **JWT**로 기본 구현하고, 내부 어드민 전용이면 토글로 끌 수 있게 해도 될까요?

### 8.8 신규 Task 목록 (실행 규칙: 한 번에 한 가지)
- [ ] T5. DB 마이그레이션 SQL 작성 및 적용 (reservations 컬럼/ENUM/트리거, seat_status, reservation_events)
- [ ] T6. 상태 머신/이벤트 로깅 구현 (`checked_in` 이후 역전 금지, `updated_at` 트리거 연동)
- [ ] T7. 토큰 생성(8자리 Base36) + 발급 API + 중복 재시도 로직 구현
- [ ] T8. QR 이미지 생성 API (PNG 기본, base64 옵션)
- [ ] T9. 좌석별 QR UI (Zone→Row 아코디언, 링크 복사, PNG 다운로드)
- [ ] T10. QA 스크립트(E2E/Smoke) 작성 및 실행
