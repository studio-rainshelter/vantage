# VANTAGE 랜딩 페이지 콘텐츠

---

## Hero Section

### 헤드라인
**이미지 얼굴 익명화 도구**

### 서브 헤드라인
MediaPipe 기반 얼굴 감지로 이미지 속 얼굴을 모자이크 또는 블러 처리합니다.  
개인 프로젝트로 개발된 오픈소스 데스크톱 앱입니다.

### CTA 버튼
- **GitHub에서 다운로드** (Primary)

---

## 주요 기능

### 1. 자동 얼굴 감지
MediaPipe BlazeFace를 사용해 이미지 속 얼굴을 자동으로 찾습니다.
- Short Range: 근거리 촬영용 (약 2m 이내)
- Full Range: 단체사진/원거리용 (약 5m 이내)

### 2. 배치 처리
폴더를 드래그 앤 드롭하면 여러 이미지를 한 번에 불러올 수 있습니다.

### 3. 수동 편집
AI가 놓친 영역이나 얼굴 외 민감 정보(번호판, 문서 등)를 직접 지정할 수 있습니다.
- 사각형 / 타원 / 올가미 도구

### 4. 모드 선택
| 모드 | 설명 |
|------|------|
| Auto | 자동 감지 영역만 처리 |
| Manual | 수동 지정 영역만 처리 |
| Override | 수동 영역 우선, 없으면 자동 |
| Append | 자동 + 수동 모두 처리 |

### 5. 효과 종류
- **모자이크**: 픽셀 블록 처리
- **가우시안 블러**: 흐림 처리

### 6. 다국어 지원
영어 / 한국어 전환 가능

---

## 사용 사례

- 블로그/SNS 업로드 시 제3자 얼굴 블러 처리
- 부동산 사진에서 거주자 익명화
- 연구/보고서용 이미지 비식별화
- 유튜브 썸네일 익명화

---

## 기술 스택

| 분야 | 기술 |
|------|------|
| 언어 | Python 3.10+ |
| UI | PySide6 |
| 비전 | MediaPipe, OpenCV |
| OS | Windows 10/11 |

---

## 설치 방법

### 개발 버전 실행
```bash
git clone https://github.com/studio-rainshelter/vantage.git
cd vantage
pip install -r requirements.txt
python main.py
```

---

## 사용 방법

1. 이미지 또는 폴더를 드래그 앤 드롭
2. 툴바에서 "자동 감지" 클릭
3. "모자이크" 또는 "블러" 선택
4. 저장

---

## 라이선스

MIT License - [Studio RainShelter](https://github.com/studio-rainshelter)

---

## 알려진 제한사항

- Windows 전용 (macOS/Linux 미지원)
- 극단적인 각도나 가려진 얼굴은 감지 어려움
- 비디오 처리 미지원

---

*© 2025 Studio RainShelter*
