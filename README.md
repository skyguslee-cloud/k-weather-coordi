# k-weather-coordi — 날씨 맞춤 코디 추천 스킬

한국 20·30·40대 여성을 위한 Claude 스킬이에요. 나이대·상황·체형 고민·선호 스타일을 짧게 묻고, 기상청 예보(최저·최고기온, 일교차, 비, 바람, 체감온도)를 확인해서 **한국 계절감에 맞는 코디 2~3벌**을 이유와 함께 추천해요.

- 출근(정장·비즈니스 캐주얼·자율 복장), 하객, 상견례, 면접, 데이트, 조문, 학부모 모임, 여행 등 상황별 규칙
- 환절기 일교차, 장마, 폭염, 한파, 눈, 바람 대응
- 체형 고민별 실루엣 팁(평가하지 않고, 원하는 인상을 만드는 방향)
- 쇼핑몰을 검색하거나 긁어오지 않아요. 브랜드·상품 링크 대신 누구나 찾을 수 있는 일반 명칭으로 알려줘요.

## 이렇게 말하면 써요

- "오늘 뭐 입지?"
- "내일 서울 출근룩 추천해줘. 비즈니스 캐주얼이고 미니멀한 스타일 좋아해"
- "모레 수원에서 친구 결혼식 가요. 하객룩 추천해줘"
- "장마철 출근 코디 알려줘"

## 설치

Claude Code(CLI·데스크톱 앱)에서 쓰는 스킬이에요. 아래 중 하나로 설치해요.

**모든 폴더에서 쓰기**

```bash
git clone https://github.com/skyguslee-cloud/k-weather-coordi.git ~/.claude/skills/k-weather-coordi
```

**특정 프로젝트 폴더에서만 쓰기**

```bash
git clone https://github.com/skyguslee-cloud/k-weather-coordi.git .claude/skills/k-weather-coordi
```

설치 후 Claude Code에서 새 대화를 열면 인식돼요.

### 필요한 것

- Python 3.8 이상 (날씨 스크립트용, 추가 패키지 없음)
- 인터넷 연결 (기상청 예보 조회)
- API 키는 필요 없어요.

## 구성

| 파일 | 내용 |
|---|---|
| `SKILL.md` | 진행 순서: 짧은 인터뷰 → 날씨 조회 → 규칙 적용 → 코디 2~3벌 |
| `scripts/today_weather.py` | 오늘·내일·모레 날씨를 코디에 필요한 값으로 요약 |
| `references/temperature-layers.md` | 기온 구간별 옷차림, 일교차·비 대응 |
| `references/korean-seasons.md` | 환절기·장마·폭염·한파·눈·바람 규칙 |
| `references/occasions.md` | 상황별 예절과 코디 규칙 |
| `references/body-and-age.md` | 체형 고민별 팁, 나이대별 접근, 색 고르기 |

날씨 스크립트만 따로 써볼 수도 있어요.

```bash
python scripts/today_weather.py --city 서울
python scripts/today_weather.py --city 부산 --day tomorrow
python scripts/today_weather.py --lat 37.4979 --lon 127.0276 --day dayafter
```

## 데이터 출처와 감사

날씨는 기상청 단기예보·초단기실황을 [NomaDamas/k-skill](https://github.com/NomaDamas/k-skill)의 공용 중계 서버(`k-skill-proxy.nomadamas.org`)를 통해 받아요. 이 서버가 멈추면 날씨 조회가 실패하고, 스킬은 수치를 지어내지 않고 그 사실을 알려요. 직접 운영하는 중계 서버가 있으면 `KSKILL_PROXY_BASE_URL` 환경변수로 바꿀 수 있어요.

## 개인정보 안내

- 날씨를 조회할 때 **지역의 위도·경도**가 위 공용 중계 서버로 전송돼요. 그 밖의 정보(이름, 나이대, 체형, 대화 내용)는 보내지 않아요.
- 스크립트는 날씨 조회만 하고, 내 PC의 파일을 읽거나 다른 곳으로 보내지 않아요.
- 동네가 드러나는 게 싫으면 구·동 대신 시 단위(`--city 서울`)로 물어보세요.

## 라이선스

MIT
