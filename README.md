# guitteum-mcp

대통령 연설문 수집용 MCP(Model Context Protocol) 서버.

[data.go.kr 정책브리핑 연설문 API](https://www.data.go.kr/)에서 연설문을 수집하여 MCP 프로토콜(stdio)로 제공한다.
Spring Boot 백엔드(`guitteum-backend`)의 `SpeechMcpClient`가 이 서버를 subprocess로 실행하여 통신한다.

## 기술 스택

| 항목 | 기술 |
|------|------|
| Language | Python 3.10+ |
| MCP SDK | mcp[cli] 1.x (FastMCP) |
| HTTP Client | httpx |
| XML Parser | xmltodict |
| Build | hatchling |
| Transport | stdio (JSON-RPC) |

## 프로젝트 구조

```
src/guitteum_mcp/
├── __init__.py        # 패키지 진입점
├── __main__.py        # python -m 진입점
├── server.py          # FastMCP 서버 + 도구 등록
├── api_client.py      # data.go.kr API 호출
├── mapper.py          # XML → SpeechData 변환
├── models.py          # Pydantic 응답 스키마
├── pagination.py      # 3일 윈도우 순회 + 캐시
└── config.py          # 환경변수 로딩
```

## MCP 도구

### `list_speeches`

전체 연설문을 페이지 단위로 반환한다.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `page` | int | 1 | 페이지 번호 |
| `per_page` | int | 100 | 페이지당 항목 수 |

### `search_speeches`

대통령명으로 필터링된 연설문을 반환한다.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `president` | str | - | 대통령 이름 (예: "윤석열") |
| `page` | int | 1 | 페이지 번호 |
| `per_page` | int | 100 | 페이지당 항목 수 |

## 설치 및 실행

### 사전 요구사항

- Python 3.10+
- [data.go.kr](https://www.data.go.kr/) API 인증키

### 설치

```bash
pip install -e .
```

### 실행

```bash
# 환경변수로 API 키 전달
DATA_GO_API_KEY=your_key guitteum-mcp

# 또는 python -m
DATA_GO_API_KEY=your_key python -m guitteum_mcp
```

### 백엔드 연동 (로컬 개발)

`application.yml`:

```yaml
data-go:
  api-key: ${DATA_GO_API_KEY:}
  mcp-command: uv
  mcp-args: --directory ../guitteum-mcp run guitteum-mcp
```

### 배포

```yaml
data-go:
  mcp-command: uvx
  mcp-args: guitteum-mcp
```

## 테스트

```bash
pip install pytest
pytest tests/ -v
```

## 설계 노트

- **3일 윈도우**: data.go.kr API가 3일 초과 조회를 거부하므로, 2008-02-25부터 오늘까지 3일 단위로 반복 호출하여 인메모리 캐시에 적재한다.
- **stdout 보호**: MCP stdio 트랜스포트가 stdout을 사용하므로, 모든 로깅은 stderr로 출력한다.
- **대통령 매핑**: 임기 날짜 기반으로 이명박~윤석열 자동 판별한다.
