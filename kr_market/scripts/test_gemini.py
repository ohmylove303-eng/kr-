import os
import sys
import json
from dotenv import load_dotenv

# 로깅 설정
import logging
logging.basicConfig(level=logging.INFO)

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
os.chdir(project_root)

# Load env
load_dotenv()
print(f"GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')[:10]}...")

from kr_market.kr_ai_analyzer import analyze_with_gemini

# 테스트 데이터
signal_data = {
    'name': '삼성전자',
    'ticker': '005930',
    'score': 85,
    'contraction_ratio': 0.4,
    'foreign_5d': 100000000,
    'inst_5d': 50000000,
    'entry_price': 80000,
    'current_price': 85000,
    'return_pct': 6.25
}

market_indices = {}
news = []

print("=== Gemini 분석 시작 ===")
result = analyze_with_gemini(signal_data, market_indices, news)
print("=== Gemini 분석 결과 ===")
print(json.dumps(result, indent=2, ensure_ascii=False))
