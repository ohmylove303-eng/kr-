"""
NICE v6.x - AI 기반 한국 주식 심층 분석 시스템
AI Seminar + GPT + 천대들의 질문법 + Ralph Prophet 분석 통합

특징:
1. 실시간 뉴스 수집 + AI 분석
2. 단기/중기/장기 전략 자동 생성
3. 시장 파이 차트 (실시간 업데이트)
4. 외인/왠인 매수/매도 추적
5. 모든 펀더멘탈/퀀트 지표
6. 천대들의 질문법 (5Why, SCAMPER, etc.)
7. Ralph Prophet 심층 분석 체계
8. 지속적 보완 및 고도화

버전: v6.x Advanced AI Edition
작성일: 2026-01-05
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import threading
from collections import defaultdict
import json
import re


# ============================================
# 1. AI 세미나 분석 시스템
# ============================================

@dataclass
class AISeminar:
    """AI 세미나 자료"""
    symbol: str
    date: str
    title: str
    content: str              # AI가 생성한 분석 내용
    key_points: List[str]     # 핵심 포인트
    ai_engine: str = "GPT-4"  # 사용 AI 엔진
    confidence: float = 0.0   # 신뢰도


class AISeminarGenerator:
    """AI 세미나 생성기"""
    
    def __init__(self):
        self.seminars: Dict[str, List[AISeminar]] = defaultdict(list)
    
    def generate_seminar(self, symbol: str, stock_data: Dict) -> AISeminar:
        """AI 세미나 자료 생성"""
        
        # 시뮬레이션: 실제로는 GPT API 호출
        prompt = self._build_prompt(symbol, stock_data)
        
        # GPT 분석 (시뮬레이션)
        analysis = self._simulate_gpt_analysis(symbol, stock_data)
        
        seminar = AISeminar(
            symbol=symbol,
            date=datetime.now().isoformat(),
            title=analysis['title'],
            content=analysis['content'],
            key_points=analysis['key_points'],
            confidence=analysis['confidence']
        )
        
        self.seminars[symbol].append(seminar)
        return seminar
    
    def _build_prompt(self, symbol: str, stock_data: Dict) -> str:
        """GPT 프롬프트 생성"""
        return f"""
        분석 대상: {stock_data.get('name', symbol)}
        
        요구사항:
        1. 현재 시장 상황 분석
        2. 이 기업의 경쟁력 분석
        3. 산업 트렌드 분석
        4. 투자 시각 제시
        5. 리스크 요소 분석
        
        데이터:
        - PER: {stock_data.get('per', 'N/A')}
        - PBR: {stock_data.get('pbr', 'N/A')}
        - ROE: {stock_data.get('roe', 'N/A')}
        - 부채비율: {stock_data.get('debt_ratio', 'N/A')}%
        - 성장률: {stock_data.get('growth_rate', 'N/A')}%
        
        이 데이터를 바탕으로 전문가 수준의 분석 보고서를 생성해주세요.
        """
    
    def _simulate_gpt_analysis(self, symbol: str, stock_data: Dict) -> Dict:
        """GPT 분석 시뮬레이션"""
        
        per = stock_data.get('per', 15)
        growth = stock_data.get('growth_rate', 0)
        roe = stock_data.get('roe', 10)
        
        # 평가
        if per < 12 and growth > 20:
            assessment = "매력적인 성장주"
            confidence = 0.95
        elif per < 15 and roe > 15:
            assessment = "우수한 수익성 기업"
            confidence = 0.90
        elif growth > 30:
            assessment = "고성장 기업"
            confidence = 0.85
        else:
            assessment = "중립적 평가"
            confidence = 0.70
        
        return {
            'title': f"{stock_data.get('name', symbol)} - {assessment}",
            'content': f"""
【 시장 분석 】
현재 {stock_data.get('name', symbol)}은 {assessment}로 평가됩니다.

【 핵심 강점 】
1. PER {per}배 - {'저평가 상태' if per < 15 else '고평가 상태'}
2. 성장률 {growth}% - {'높은 성장성' if growth > 20 else '보통 수준'}
3. ROE {roe}% - {'우수한 수익성' if roe > 15 else '개선 필요'}

【 투자 관점 】
단기: {'매수' if per < 15 else '중립'}
중기: {'매수' if growth > 15 else '보유'}
장기: {'강력 추천' if roe > 15 and growth > 10 else '검토'}

【 리스크 요소 】
1. 시장 변동성 위험
2. 산업 변화 리스크
3. 경기 민감도
            """,
            'key_points': [
                f"PER {per}배: {'저평가' if per < 15 else '고평가'} 신호",
                f"성장률 {growth}%: {'높은 성장' if growth > 20 else '보통'} 수준",
                f"ROE {roe}%: {'우수' if roe > 15 else '보통'} 수익성",
                f"평가: {assessment}"
            ],
            'confidence': confidence
        }


# ============================================
# 2. 천대들의 질문법 (5Why, SCAMPER)
# ============================================

class GeniusQuestionMethod:
    """천대들의 질문법"""
    
    @staticmethod
    def five_why_analysis(symbol: str, problem: str, stock_data: Dict) -> Dict:
        """5Why 분석"""
        return {
            'method': '5Why Analysis',
            'symbol': symbol,
            'problem': problem,
            'analysis': [
                {
                    'level': 1,
                    'why': f"왜 {stock_data.get('name')}의 {problem}일까?",
                    'answer': f"시장 환경 때문에"
                },
                {
                    'level': 2,
                    'why': "시장 환경은 구체적으로 뭘까?",
                    'answer': f"산업 성장률, 경쟁 강도, 정부 정책"
                },
                {
                    'level': 3,
                    'why': "이것이 우리 회사에 어떤 영향?",
                    'answer': f"매출, 이익, 현금흐름에 직접 영향"
                },
                {
                    'level': 4,
                    'why': "그럼 근본 원인은?",
                    'answer': f"경영진의 전략, 기술력, 브랜드 가치"
                },
                {
                    'level': 5,
                    'why': "이를 해결하려면?",
                    'answer': f"혁신, 효율화, M&A, 신사업 진출"
                }
            ]
        }
    
    @staticmethod
    def scamper_analysis(symbol: str, stock_data: Dict) -> Dict:
        """SCAMPER 분석"""
        return {
            'method': 'SCAMPER',
            'symbol': symbol,
            'dimensions': {
                'Substitute': {
                    'question': '현재 제품/서비스를 다른 것으로 대체할 수 있나?',
                    'insight': '기술 변화, 소비 트렌드'
                },
                'Combine': {
                    'question': '다른 사업과 결합하면?',
                    'insight': '시너지, 신시장 창출'
                },
                'Adapt': {
                    'question': '다른 산업의 아이디어 적용 가능?',
                    'insight': '혁신, 차별화'
                },
                'Modify': {
                    'question': '제품/서비스 변경 가능?',
                    'insight': '품질 향상, 원가 절감'
                },
                'Put': {
                    'question': '새로운 용도 발견 가능?',
                    'insight': '시장 확대, 고객층 확대'
                },
                'Eliminate': {
                    'question': '불필요한 기능 제거?',
                    'insight': '원가 절감, 단순화'
                },
                'Reverse': {
                    'question': '반대로 생각하면?',
                    'insight': '새로운 기회, 위협 분석'
                }
            }
        }


# ============================================
# 3. Ralph Prophet 심층 분석
# ============================================

@dataclass
class RalphProphetAnalysis:
    """Ralph Prophet 분석"""
    symbol: str
    timestamp: str
    
    # 시장 분석
    market_trend: str          # 상승/중립/하락
    market_strength: float     # 0-100
    
    # 기업 분석
    business_quality: float    # 사업 질 (0-100)
    competitive_moat: float    # 경쟁력 (0-100)
    management_quality: float  # 경영진 질 (0-100)
    
    # 가치 분석
    intrinsic_value: float     # 내재가치
    current_price: float
    margin_of_safety: float    # 안전 마진 (%)
    
    # 전략
    short_term_strategy: str   # 단기 전략
    mid_term_strategy: str     # 중기 전략
    long_term_strategy: str    # 장기 전략
    
    # 위험
    risk_factors: List[str]    # 위험 요소
    opportunity_factors: List[str]  # 기회 요소
    
    recommendation: str        # 최종 추천
    conviction_level: str      # 확신 수준 (High/Medium/Low)


class RalphProphetAnalyzer:
    """Ralph Prophet 분석기"""
    
    def analyze(self, symbol: str, stock_data: Dict, financial_data: Dict) -> RalphProphetAnalysis:
        """종합 분석"""
        
        # 1. 시장 분석
        market_trend, market_strength = self._analyze_market(stock_data)
        
        # 2. 기업 분석
        business_quality = self._evaluate_business_quality(financial_data)
        competitive_moat = self._evaluate_competitive_moat(stock_data, financial_data)
        management_quality = self._evaluate_management_quality(financial_data)
        
        # 3. 가치 분석
        intrinsic_value = self._calculate_intrinsic_value(financial_data)
        current_price = stock_data.get('current_price', 0)
        margin_of_safety = ((intrinsic_value - current_price) / current_price * 100) if current_price > 0 else 0
        
        # 4. 전략 수립
        strategies = self._develop_strategies(
            stock_data, financial_data,
            business_quality, competitive_moat,
            margin_of_safety
        )
        
        # 5. 위험/기회 분석
        risks = self._identify_risks(stock_data, financial_data)
        opportunities = self._identify_opportunities(stock_data, financial_data)
        
        # 6. 최종 추천
        recommendation, conviction = self._generate_recommendation(
            business_quality, competitive_moat, management_quality,
            margin_of_safety, market_strength
        )
        
        return RalphProphetAnalysis(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            market_trend=market_trend,
            market_strength=market_strength,
            business_quality=business_quality,
            competitive_moat=competitive_moat,
            management_quality=management_quality,
            intrinsic_value=intrinsic_value,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            short_term_strategy=strategies['short_term'],
            mid_term_strategy=strategies['mid_term'],
            long_term_strategy=strategies['long_term'],
            risk_factors=risks,
            opportunity_factors=opportunities,
            recommendation=recommendation,
            conviction_level=conviction
        )
    
    def _analyze_market(self, stock_data: Dict) -> Tuple[str, float]:
        """시장 분석"""
        change_rate = stock_data.get('change_rate', 0)
        
        if change_rate > 2:
            trend = "상승"
            strength = min(100, 50 + change_rate * 10)
        elif change_rate < -2:
            trend = "하락"
            strength = max(0, 50 + change_rate * 10)
        else:
            trend = "중립"
            strength = 50
        
        return trend, strength
    
    def _evaluate_business_quality(self, financial_data: Dict) -> float:
        """사업 질 평가"""
        
        roe = financial_data.get('roe', 0)
        roa = financial_data.get('roa', 0)
        margin = financial_data.get('net_margin', 0)
        
        # 스코어 계산
        score = 0
        
        if roe > 20:
            score += 35
        elif roe > 15:
            score += 25
        elif roe > 10:
            score += 15
        else:
            score += 5
        
        if roa > 10:
            score += 35
        elif roa > 5:
            score += 25
        elif roa > 2:
            score += 15
        else:
            score += 5
        
        if margin > 20:
            score += 30
        elif margin > 10:
            score += 20
        elif margin > 5:
            score += 10
        else:
            score += 5
        
        return min(100, score)
    
    def _evaluate_competitive_moat(self, stock_data: Dict, financial_data: Dict) -> float:
        """경쟁력(Moat) 평가"""
        
        score = 0
        
        # 브랜드 (PBR 기반)
        pbr = stock_data.get('pbr', 1.0)
        if pbr > 2.0:
            score += 30  # 강한 브랜드
        elif pbr > 1.5:
            score += 20
        else:
            score += 10
        
        # 수익성 (ROE 기반)
        roe = financial_data.get('roe', 0)
        if roe > 20:
            score += 30
        elif roe > 15:
            score += 20
        else:
            score += 10
        
        # 성장률
        growth = financial_data.get('growth_rate', 0)
        if growth > 30:
            score += 25
        elif growth > 15:
            score += 15
        else:
            score += 5
        
        # 시장 점유율 (시가총액)
        market_cap = stock_data.get('market_cap', 0)
        if market_cap > 100:  # 조원
            score += 15
        elif market_cap > 50:
            score += 10
        else:
            score += 5
        
        return min(100, score)
    
    def _evaluate_management_quality(self, financial_data: Dict) -> float:
        """경영진 질 평가"""
        
        score = 50  # 기본값
        
        # 효율성 개선
        if financial_data.get('revenue_growth', 0) > financial_data.get('cost_growth', 0):
            score += 20
        
        # 수익성 개선
        if financial_data.get('net_margin', 0) > financial_data.get('prev_net_margin', 0):
            score += 20
        
        # ROE 개선
        if financial_data.get('roe', 0) > financial_data.get('prev_roe', 0):
            score += 10
        
        return min(100, score)
    
    def _calculate_intrinsic_value(self, financial_data: Dict) -> float:
        """내재가치 계산"""
        
        eps = financial_data.get('eps', 0)
        growth = financial_data.get('growth_rate', 0)
        
        if eps <= 0:
            return 0
        
        # PEG 기반 공정 PER 계산
        fair_per = 30 - growth if growth < 30 else 0
        fair_per = max(10, fair_per)
        
        intrinsic_value = eps * fair_per
        
        return intrinsic_value
    
    def _develop_strategies(self, stock_data: Dict, financial_data: Dict,
                          business_quality: float, competitive_moat: float,
                          margin_of_safety: float) -> Dict[str, str]:
        """전략 수립"""
        
        strategies = {}
        
        # 단기 (1-3개월)
        if margin_of_safety > 30:
            strategies['short_term'] = "적극 매수 - 충분한 안전 마진"
        elif margin_of_safety > 15:
            strategies['short_term'] = "매수 - 양호한 가치"
        elif margin_of_safety > 0:
            strategies['short_term'] = "중립 - 공정가치 근처"
        else:
            strategies['short_term'] = "매도 - 과평가 상태"
        
        # 중기 (3-12개월)
        if business_quality > 70 and competitive_moat > 70:
            strategies['mid_term'] = "강력 매수 - 우수한 기업"
        elif business_quality > 60 and competitive_moat > 60:
            strategies['mid_term'] = "매수 - 양호한 펀더멘탈"
        else:
            strategies['mid_term'] = "보유 - 추가 모니터링"
        
        # 장기 (1년 이상)
        growth = financial_data.get('growth_rate', 0)
        if business_quality > 75 and growth > 20:
            strategies['long_term'] = "강력 추천 - 장기 성장주"
        elif business_quality > 70:
            strategies['long_term'] = "추천 - 장기 보유 가치"
        else:
            strategies['long_term'] = "검토 필요 - 성장성 재평가"
        
        return strategies
    
    def _identify_risks(self, stock_data: Dict, financial_data: Dict) -> List[str]:
        """위험 요소 식별"""
        
        risks = []
        
        # 밸류에이션 위험
        per = stock_data.get('per', 0)
        if per > 30:
            risks.append(f"고평가 위험 (PER {per}배)")
        
        # 안정성 위험
        debt_ratio = financial_data.get('debt_ratio', 0)
        if debt_ratio > 100:
            risks.append(f"높은 부채 위험 (부채비율 {debt_ratio}%)")
        
        # 성장 정체 위험
        growth = financial_data.get('growth_rate', 0)
        if growth < 5:
            risks.append(f"성장 정체 위험 (성장률 {growth}%)")
        
        # 산업 위험
        sector = stock_data.get('sector', '')
        if sector in ['반도체', '디스플레이']:
            risks.append(f"{sector} 산업 순환 위험")
        
        return risks
    
    def _identify_opportunities(self, stock_data: Dict, financial_data: Dict) -> List[str]:
        """기회 요소 식별"""
        
        opportunities = []
        
        # 저평가 기회
        per = stock_data.get('per', 0)
        if per < 12:
            opportunities.append(f"저평가 기회 (PER {per}배)")
        
        # 성장 기회
        growth = financial_data.get('growth_rate', 0)
        if growth > 25:
            opportunities.append(f"고성장 기회 (성장률 {growth}%)")
        
        # 배당 기회
        dividend = stock_data.get('dividend_yield', 0)
        if dividend > 3:
            opportunities.append(f"배당 수익 기회 ({dividend}%)")
        
        # 신사업
        opportunities.append("신사업 진출 기회 검토")
        
        return opportunities
    
    def _generate_recommendation(self, business_quality: float, competitive_moat: float,
                               management_quality: float, margin_of_safety: float,
                               market_strength: float) -> Tuple[str, str]:
        """최종 추천"""
        
        overall_score = (
            business_quality * 0.3 +
            competitive_moat * 0.3 +
            management_quality * 0.2 +
            margin_of_safety * 0.2
        )
        
        if overall_score > 75:
            recommendation = "강력 매수"
            conviction = "High"
        elif overall_score > 60:
            recommendation = "매수"
            conviction = "Medium"
        elif overall_score > 45:
            recommendation = "보유"
            conviction = "Medium"
        else:
            recommendation = "매도"
            conviction = "Low"
        
        return recommendation, conviction


# ============================================
# 4. 뉴스 및 시장 데이터 수집
# ============================================

@dataclass
class MarketNews:
    """시장 뉴스"""
    symbol: str
    date: str
    title: str
    source: str
    content: str
    sentiment: str          # positive/neutral/negative
    importance: int         # 1-5


@dataclass
class ForeignTraderActivity:
    """외인 거래 활동"""
    symbol: str
    date: str
    buy_volume: int         # 매수량
    sell_volume: int        # 매도량
    net_flow: int           # 순매수/매도
    buy_rate: float         # 매수 비율 (%)


class MarketDataCollector:
    """시장 데이터 수집기"""
    
    def __init__(self):
        self.news: Dict[str, List[MarketNews]] = defaultdict(list)
        self.trader_activity: Dict[str, List[ForeignTraderActivity]] = defaultdict(list)
    
    def collect_news(self, symbol: str) -> List[MarketNews]:
        """뉴스 수집 (시뮬레이션)"""
        
        # 실제로는 언론사 API, 네이버, 카카오 등에서 수집
        sample_news = [
            {
                'title': f'{symbol} 기업, 분기 실적 시장 예상 상회',
                'source': '한국경제',
                'content': '...',
                'sentiment': 'positive',
                'importance': 4
            },
            {
                'title': f'{symbol} 산업, 규제 이슈 우려',
                'source': '매경',
                'content': '...',
                'sentiment': 'negative',
                'importance': 3
            }
        ]
        
        news_objects = []
        for n in sample_news:
            news = MarketNews(
                symbol=symbol,
                date=datetime.now().isoformat(),
                title=n['title'],
                source=n['source'],
                content=n['content'],
                sentiment=n['sentiment'],
                importance=n['importance']
            )
            news_objects.append(news)
            self.news[symbol].append(news)
        
        return news_objects
    
    def collect_trader_activity(self, symbol: str) -> Optional[ForeignTraderActivity]:
        """외인 거래 수집 (시뮬레이션)"""
        
        # 실제로는 한국거래소 데이터에서 수집
        buy_volume = np.random.randint(100000, 1000000)
        sell_volume = np.random.randint(100000, 1000000)
        
        activity = ForeignTraderActivity(
            symbol=symbol,
            date=datetime.now().isoformat(),
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            net_flow=buy_volume - sell_volume,
            buy_rate=(buy_volume / (buy_volume + sell_volume)) * 100
        )
        
        self.trader_activity[symbol].append(activity)
        return activity


# ============================================
# 5. 시장 파이 차트 (실시간)
# ============================================

@dataclass
class MarketPieChart:
    """시장 파이 차트"""
    timestamp: str
    sectors: Dict[str, float]      # 산업군별 시가총액 비율
    market_cap_dist: Dict[str, float]  # 시가총액 분포
    top_10_stocks: List[Tuple[str, float]]  # Top 10 주식
    foreign_ownership: Dict[str, float]  # 외인 소유 비율


class MarketPieGenerator:
    """시장 파이 차트 생성기"""
    
    def generate_pie_chart(self, stocks: List[Dict]) -> MarketPieChart:
        """파이 차트 생성"""
        
        # 산업군별 분류
        sectors = defaultdict(float)
        for stock in stocks:
            sector = stock.get('sector', 'Other')
            market_cap = stock.get('market_cap', 0)
            sectors[sector] += market_cap
        
        # 시가총액별 분포
        total_cap = sum(sectors.values())
        sector_dist = {
            sector: (cap / total_cap * 100) if total_cap > 0 else 0
            for sector, cap in sectors.items()
        }
        
        # Top 10 주식
        sorted_stocks = sorted(
            [(s.get('name'), s.get('market_cap', 0)) for s in stocks],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # 외인 소유 비율 (시뮬레이션)
        foreign_ownership = {
            s.get('symbol'): np.random.uniform(5, 35)
            for s in stocks[:5]
        }
        
        return MarketPieChart(
            timestamp=datetime.now().isoformat(),
            sectors=dict(sectors),
            market_cap_dist=sector_dist,
            top_10_stocks=sorted_stocks,
            foreign_ownership=foreign_ownership
        )


# ============================================
# 6. 종합 분석 시스템
# ============================================

class ComprehensiveStockAnalyzer:
    """종합 주식 분석기"""
    
    def __init__(self):
        self.ai_seminar = AISeminarGenerator()
        self.genius_method = GeniusQuestionMethod()
        self.ralph_analyzer = RalphProphetAnalyzer()
        self.news_collector = MarketDataCollector()
        self.pie_generator = MarketPieGenerator()
    
    def analyze_comprehensively(self, symbol: str, stock_data: Dict, financial_data: Dict) -> Dict:
        """종합 분석"""
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            
            # 1. AI 세미나
            'ai_seminar': asdict(self.ai_seminar.generate_seminar(symbol, stock_data)),
            
            # 2. 천대들의 질문법
            'five_why': self.genius_method.five_why_analysis(
                symbol, 'PER 수준 고평가', stock_data
            ),
            'scamper': self.genius_method.scamper_analysis(symbol, stock_data),
            
            # 3. Ralph Prophet 분석
            'ralph_analysis': asdict(
                self.ralph_analyzer.analyze(symbol, stock_data, financial_data)
            ),
            
            # 4. 뉴스 및 시장 데이터
            'recent_news': [asdict(n) for n in self.news_collector.collect_news(symbol)],
            'trader_activity': asdict(self.news_collector.collect_trader_activity(symbol)),
            
            # 5. 시장 파이 차트
            # 'market_pie': asdict(self.pie_generator.generate_pie_chart([stock_data]))
        }
        
        return analysis


# ============================================
# 테스트
# ============================================

if __name__ == '__main__':
    print("✅ NICE v6.x AI 기반 분석 시스템 로드됨\n")
    
    # 테스트 데이터
    test_stock = {
        'symbol': '005930',
        'name': '삼성전자',
        'sector': '반도체',
        'current_price': 72000,
        'per': 13.5,
        'pbr': 1.2,
        'market_cap': 450.0,
        'dividend_yield': 3.1,
        'change_rate': 2.86
    }
    
    test_financial = {
        'roe': 7.4,
        'roa': 2.7,
        'net_margin': 13.5,
        'growth_rate': 32.4,
        'debt_ratio': 64.3,
        'eps': 5333,
        'revenue_growth': 5.2,
        'prev_net_margin': 12.5,
        'prev_roe': 7.0
    }
    
    # 종합 분석
    analyzer = ComprehensiveStockAnalyzer()
    result = analyzer.analyze_comprehensively('005930', test_stock, test_financial)
    
    print("【 AI 세미나 】")
    print(f"제목: {result['ai_seminar']['title']}")
    print(f"신뢰도: {result['ai_seminar']['confidence']:.1%}\n")
    
    print("【 Ralph Prophet 분석 】")
    ralph = result['ralph_analysis']
    print(f"사업 질: {ralph['business_quality']:.1f}/100")
    print(f"경쟁력: {ralph['competitive_moat']:.1f}/100")
    print(f"경영진 질: {ralph['management_quality']:.1f}/100")
    print(f"안전 마진: {ralph['margin_of_safety']:.1f}%")
    print(f"추천: {ralph['recommendation']} ({ralph['conviction_level']})\n")
    
    print("【 전략 】")
    print(f"단기: {ralph['short_term_strategy']}")
    print(f"중기: {ralph['mid_term_strategy']}")
    print(f"장기: {ralph['long_term_strategy']}\n")
    
    print("✅ 분석 완료")
