# VANTAGE

**V**isual **A**nonymization & **T**actical **G**raphics **E**ditor

대량의 이미지 데이터에서 인물 식별 정보를 신속하고 정확하게 익명화(Mosaic/Blur)하는 산업용 파이썬 어플리케이션.

## Design Philosophy

**Industrial Brutalism** - 날카로운 그리드, 고대비 색상, 노출된 구조를 통해 "도구로서의 정체성"을 강조합니다.

## Features

- 🎯 **자동 얼굴 감지**: MediaPipe 기반 실시간 얼굴 인식
- 🖼️ **대량 배치 처리**: 수천 장의 이미지 동시 처리
- ✏️ **수동 편집 모드**: 정밀한 ROI 지정 가능
- 🔄 **Hybrid 로직**: Auto + Manual 조합 지원
- 🌐 **다국어 지원**: English / 한국어

## Requirements

- Python 3.10+
- Windows 10/11

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

## Tech Stack

- **UI**: PySide6 (Qt for Python)
- **Vision**: MediaPipe, OpenCV
- **Build**: PyInstaller / Nuitka

## License

MIT License - Studio RainShelter
