# kr_market/theme_manager.py
class ThemeManager:
    """
    Manages future trend themes for Korean stocks.
    Themes: Defense (방산), Semiconductor (반도체/AI), AI Power Infra (전력설비)
    """
    
    THEMES = {
        '방산': [
            '012450', # 한화에어로스페이스
            '079550', # LIG넥스원
            '064350', # 현대로템
            '047810', # 한국항공우주
            '272210', # 한화시스템
            '059960', # 코츠테크놀로지
            '103140', # 풍산
        ],
        '반도체': [
            '005930', # 삼성전자
            '000660', # SK하이닉스
            '042700', # 한미반도체
            '403870', # HPSP
            '095340', # ISC
            '005290', # 동진쎄미켐
            '058470', # 리노공업
            '000990', # DB하이텍
        ],
        'AI전력': [
            '010120', # LS ELECTRIC
            '267260', # HD현대일렉트릭
            '298040', # 효성중공업
            '000500', # 가온전선
            '001440', # 대한전선
            '006260', # LS
            '024090', # 씨에스윈드
            '103590', # 일진전기
        ],
        '조선': [
            '010140', # 삼성중공업
            '009540', # HD한국조선해양
            '329180', # HD현대중공업
            '042660', # 한화오션
        ],
        'AI인프라': [
            '035420', # NAVER (AI 서버/하이퍼클로바)
            '000660', # SK하이닉스 (HBM)
            '042700', # 한미반도체 (AI 장비)
            '403870', # HPSP
            '267260', # HD현대일렉트릭 (AI 데이터센터 변압기)
            '298040', # 효성중공업 (변압기)
            '035760', # CJ ENM (AI 콘텐츠)
            '377300', # 카카오페이 (AI 핀테크)
        ],
        '환율수혜': [
            # 방산 수출 (Defense Exports)
            '012450', # 한화에어로스페이스
            '079550', # LIG넥스원
            '047810', # 한국항공우주
            '272210', # 한화시스템
            '064350', # 현대로템
            # 조선 (Shipbuilding - USD 결제)
            '010140', # 삼성중공업
            '009540', # HD한국조선해양
            '329180', # HD현대중공업
            # 자동차 (Automotive Exports)
            '005380', # 현대차
            '000270', # 기아
            # 전자/반도체 (High Export Ratio)
            '005930', # 삼성전자
            '000660', # SK하이닉스
            # 석유화학/정유 (Oil Refining - USD 매출)
            '096770', # SK이노베이션
            '010950', # S-Oil
            # 철강 (Steel Exports)
            '005490', # POSCO홀딩스
        ],
        '바이오': [
            '068270', # 셀트리온
            '207940', # 삼성바이오로직스
            '326030', # SK바이오팜
            '145020', # 휴젤
            '141080', # 레고켐바이오
            '195940', # HK이노엔
            '086900', # 메디톡스
            '950160', # 코오롱티슈진
        ]
    }

    @staticmethod
    def get_theme(ticker):
        """Returns the theme name if the ticker belongs to a tracked theme, else None."""
        # Simple lookup
        for theme, tickers in ThemeManager.THEMES.items():
            if ticker in tickers:
                return theme
        return None

    @staticmethod
    def get_all_target_tickers():
        """Returns a set of all tickers monitored by ThemeManager."""
        all_tickers = set()
        for tickers in ThemeManager.THEMES.values():
            all_tickers.update(tickers)
        return all_tickers
