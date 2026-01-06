📑 Software Requirements Document: Project VANTAGE
1. 프로젝트 개요 (Project Overview)
프로젝트명: VANTAGE (Visual Anonymization & Tactical Graphics Editor)

핵심 목적: 대량의 이미지 데이터에서 인물 식별 정보를 신속하고 정확하게 익명화(Mosaic/Blur)하는 산업용 파이썬 어플리케이션.

디자인 철학: Industrial Brutalism. 기성 AI 툴의 부드럽고 친절한 미학을 거부하고, 날카로운 그리드, 고대비 색상, 노출된 구조를 통해 "도구로서의 정체성"을 강조함.

2. 기술 스택 및 아키텍처 (Technical Stack)
언어 및 배포: Python 3.10+, 단일 EXE 실행 파일 (PyInstaller/Nuitka 기반).

UI 프레임워크: PySide6 (Qt for Python). 정밀한 위젯 제어와 시스템 자원 접근성을 위해 선택.

컴퓨터 비전: MediaPipe (얼굴 감지), OpenCV (이미지 연산 및 렌더링).

메모리 전략: LRU(Least Recently Used) Thumbnail Cache.

수천 장의 이미지를 로드하더라도 실제 화면에 보이는 썸네일만 메모리에 상주시키며, 임계치 초과 시 오래된 데이터를 자동 해제하여 메모리 폭발을 방지함.

3. UI/UX 디자인 시스템 (Visual Specification)
3.1 타이포그래피 및 색상
Font: JetBrains Mono (수치 및 데이터), IBM Plex Sans (UI 텍스트).

Color Palette:

Base: #0F0F0F (Deep Black)

Accent: #FF3E00 (Safety Orange) - 주요 경고 및 선택 상태 표시.

Border: #2A2A2A (Hard Grey) - 1px의 날카로운 테두리.

3.2 핵심 컴포넌트
'文/A' 다국어 스위처: 우측 상단 유틸리티 바에 배치. 클릭 시 EN/KR 즉시 전환. 산업용 토글 스위치 디자인 적용.

'M' 수동 편집 마커: 썸네일 티켓 시스템을 폐기하고, 수동 편집이 적용된 이미지 썸네일 우측 상단에 두꺼운 Safety Orange 색상의 'M' 각인 오버레이.

Inspector Pane: 썸네일 더블 클릭 시 우측에서 슬라이드 인. 눈금자(Ruler)가 포함된 정밀 편집 캔버스 제공.

4. 기능적 요구사항 (Functional Requirements)
4.1 배치 로드 및 관리
폴더/파일 드래그 앤 드롭을 통한 대량 로드 지원.

비동기 썸네일 생성 및 그리드 뷰 렌더링.

4.2 지능형 모자이크 엔진
Auto Mode: MediaPipe를 활용해 사진 내 모든 얼굴을 자동으로 찾아 모자이크 처리.

Manual Mode: 사용자가 직접 영역(ROI) 지정 가능.

Hybrid Logic: 수동 편집창 내 토글을 통해 다음 중 선택:

Override: 자동 인식 결과 무시, 수동 지정 영역만 적용.

Append: 자동 인식 결과와 수동 지정 영역 모두 적용.

4.3 다국어 지원 (i18n)
기본 언어: English.

선택 언어: Korean.

텍스트 길이에 따른 UI 레이아웃 유동적 대응 (Flex-box 모델 적용).

5. 비기능적 요구사항 (Non-Functional Requirements)
성능: 1,000장 이상의 이미지 로드 시 UI 응답성 유지 (QThread 기반 비동기 처리).

안정성: 수동 편집 데이터는 내부 JSON 구조로 관리하여 프로그램 재시작 전까지 유지.

사용성: 모든 주요 기능은 단축키 연동 가능 (Brutalist UX의 효율성 강조).