"""
질문 분석 모듈
사용자 질문에서 공정정보를 추출하고 특정 가능 여부를 판단합니다.
"""
import re
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """공정정보 데이터 클래스"""
    site_id: Optional[str] = None
    factory_id: Optional[str] = None
    process_id: Optional[str] = None
    model_id: Optional[str] = None
    down_type: Optional[str] = None  # SCHEDULED, UNSCHEDULED
    down_time_minutes: Optional[float] = None  # 분 단위
    
    def is_specific(self) -> bool:
        """공정정보가 특정 가능한지 확인"""
        # 최소한 하나의 필터 조건이 있어야 함
        return any([
            self.site_id,
            self.factory_id,
            self.process_id,
            self.model_id,
            self.down_type,
            self.down_time_minutes is not None
        ])
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'site_id': self.site_id,
            'factory_id': self.factory_id,
            'process_id': self.process_id,
            'model_id': self.model_id,
            'down_type': self.down_type,
            'down_time_minutes': self.down_time_minutes
        }


class QuestionAnalyzer:
    """질문 분석 클래스"""
    
    # 사이트 ID 패턴 (ICH, CJU, WUX 등)
    SITE_PATTERNS = [
        r'\b(ICH|이천)\b',
        r'\b(CJU|청주)\b',
        r'\b(WUX|우시)\b',
        r'\b사이트[:\s]*([A-Z]{2,4})\b',
        r'\b(site|Site)[:\s]*([A-Z]{2,4})\b',
    ]
    
    # 공장 ID 패턴 (FAB1, FAB2, FAC_M16, FAC_C2F 등)
    FACTORY_PATTERNS = [
        r'(FAC[_\-][A-Z0-9]+)',  # FAC_M16, FAC_C2F 등 (word boundary 제거)
        r'\b(FAC[A-Z0-9]+)\b',  # FACM16 등 (언더스코어 없이)
        r'\b(FAB\d+|FAB\s*\d+)\b',  # FAB1, FAB 1 등
        r'공장[:\s]*([A-Z0-9_\-]+)',  # 공장: FAC_M16
        r'(factory|Factory)[:\s]*([A-Z0-9_\-]+)',  # factory: FAC_M16
    ]
    
    # 공정 ID 패턴
    PROCESS_PATTERNS = [
        r'\b(PROC[_\-]?PH|PHOTO|포토|포토리소그래피)\b',
        r'\b(PROC[_\-]?ET|ETCH|에칭)\b',
        r'\b(PROC[_\-]?TF|CVD|화학증착|ThinFilm)\b',
        r'\b(PROC[_\-]?DF|DIFFUSION|확산)\b',
        r'\b(PROC[_\-]?CM|CMP|화학기계연마)\b',
        r'\b(PROC[_\-]?IMP|IMPLANT|이온주입)\b',
        r'\b(PROC[_\-]?CLN|CLEANING|세정)\b',
        r'\b(PROC[_\-]?MI|METROLOGY|계측)\b',
        r'\b공정[:\s]*([A-Z_\-]+)\b',
        r'\b(process|Process)[:\s]*([A-Z_\-]+)\b',
    ]
    
    # 모델 ID 패턴
    MODEL_PATTERNS = [
        r'\b(MDL[_\-][A-Z0-9_]+)\b',  # MDL_KE_PRO, MDL-KE-LITE 등
        r'\b(MODEL[_\-][A-Z0-9_]+)\b',  # MODEL-KE-PRO 등
        r'\b(MODEL[-\s]?[A-Z]|모델[-\s]?[A-Z])\b',
        r'\b(model|Model)[:\s]*([A-Z0-9_-]+)\b',
    ]
    
    # 다운타임 유형 패턴
    DOWN_TYPE_PATTERNS = [
        (r'\b(계획|스케줄|SCHEDULED|scheduled)\b', 'SCHEDULED'),
        (r'\b(비계획|비스케줄|UNSCHEDULED|unscheduled)\b', 'UNSCHEDULED'),
        (r'\b(계획된|스케줄된)\b', 'SCHEDULED'),
        (r'\b(비계획된|예기치\s*않은)\b', 'UNSCHEDULED'),
    ]
    
    # 시간 패턴 (분 단위)
    TIME_PATTERNS = [
        (r'(\d+(?:\.\d+)?)\s*분', 1),  # N분
        (r'(\d+(?:\.\d+)?)\s*시간', 60),  # N시간 -> 분 변환
        (r'(\d+(?:\.\d+)?)\s*h(?:our)?s?', 60),  # Nh
        (r'(\d+(?:\.\d+)?)\s*m(?:in)?s?', 1),  # Nm
        (r'(\d+(?:\.\d+)?)\s*시간\s*(\d+(?:\.\d+)?)\s*분', None),  # N시간 M분
    ]
    
    def __init__(self):
        """초기화"""
        pass
    
    def analyze(self, question: str) -> Tuple[ProcessInfo, bool]:
        """
        질문을 분석하여 공정정보를 추출하고 특정 가능 여부를 반환
        
        Returns:
            (ProcessInfo, is_specific): 공정정보와 특정 가능 여부
        """
        logger.info(f"[질문 분석] 시작: '{question}'")
        
        process_info = ProcessInfo()
        
        # 사이트 ID 추출
        site_id = self._extract_site_id(question)
        if site_id:
            process_info.site_id = site_id
            logger.info(f"[질문 분석] 사이트 ID 추출: {site_id}")
        
        # 공장 ID 추출
        factory_id = self._extract_factory_id(question)
        if factory_id:
            process_info.factory_id = factory_id
            logger.info(f"[질문 분석] 공장 ID 추출: {factory_id}")
        
        # 공정 ID 추출
        process_id = self._extract_process_id(question)
        if process_id:
            process_info.process_id = process_id
            logger.info(f"[질문 분석] 공정 ID 추출: {process_id}")
        
        # 모델 ID 추출
        model_id = self._extract_model_id(question)
        if model_id:
            process_info.model_id = model_id
            logger.info(f"[질문 분석] 모델 ID 추출: {model_id}")
        
        # 다운타임 유형 추출
        down_type = self._extract_down_type(question)
        if down_type:
            process_info.down_type = down_type
            logger.info(f"[질문 분석] 다운타임 유형 추출: {down_type}")
        
        # 다운타임 시간 추출
        down_time = self._extract_down_time(question)
        if down_time is not None:
            process_info.down_time_minutes = down_time
            logger.info(f"[질문 분석] 다운타임 시간 추출: {down_time}분")
        
        # 특정 가능 여부 판단
        is_specific = process_info.is_specific()
        
        logger.info(f"[질문 분석] 완료 - 특정 가능: {is_specific}")
        logger.info(f"[질문 분석] 추출된 정보: {process_info.to_dict()}")
        
        return process_info, is_specific
    
    def _extract_site_id(self, text: str) -> Optional[str]:
        """사이트 ID 추출"""
        text_upper = text.upper()
        
        for pattern in self.SITE_PATTERNS:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                # 그룹이 있으면 그룹 값, 없으면 전체 매치
                site = match.group(1) if match.groups() else match.group(0)
                # 알파벳만 추출
                site = re.sub(r'[^A-Z]', '', site)
                if site:
                    return site
        
        return None
    
    def _extract_factory_id(self, text: str) -> Optional[str]:
        """공장 ID 추출"""
        text_upper = text.upper()
        
        for pattern in self.FACTORY_PATTERNS:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                factory = match.group(1) if match.groups() else match.group(0)
                # FAB 숫자 정규화
                factory = re.sub(r'FAB\s*(\d+)', r'FAB\1', factory, flags=re.IGNORECASE)
                # FAC 형식 정규화 (FAC_M16, FAC_C2F 등)
                if factory.startswith('FAC') and '_' not in factory and len(factory) > 3:
                    # FACM16 -> FAC_M16 형식으로 변환 (숫자나 알파벳이 붙어있는 경우)
                    factory = re.sub(r'FAC([A-Z])(\d+)', r'FAC_\1\2', factory)
                    factory = re.sub(r'FAC([A-Z]+)', r'FAC_\1', factory)
                elif factory.startswith('FAC') and '-' in factory:
                    # FAC-M16 -> FAC_M16
                    factory = factory.replace('-', '_')
                if factory:
                    return factory
        
        return None
    
    def _extract_process_id(self, text: str) -> Optional[str]:
        """공정 ID 추출"""
        text_upper = text.upper()
        
        # 한글 공정명 매핑 (먼저 처리)
        korean_process_map = {
            '포토': 'PROC_PH',
            '포토리소그래피': 'PROC_PH',
            '에칭': 'PROC_ET',
            '화학증착': 'PROC_TF',
            '확산': 'PROC_DF',
            '화학기계연마': 'PROC_CM',
            '이온주입': 'PROC_IMP',
            '세정': 'PROC_CLN',
            '계측': 'PROC_MI',
        }
        
        for korean, process_id in korean_process_map.items():
            if korean in text:
                return process_id
        
        # 영문 패턴 매칭
        for pattern in self.PROCESS_PATTERNS:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                process = match.group(1) if match.groups() else match.group(0)
                # PROC_ 형식인 경우 그대로 사용
                if 'PROC_' in process or 'PROC-' in process:
                    # PROC_PH -> PROC_PH, PROC-ET -> PROC_ET
                    process = re.sub(r'PROC[-_]', 'PROC_', process)
                    return process
                # 알파벳만 추출하여 PROC_ 접두사 추가
                process_clean = re.sub(r'[^A-Z]', '', process)
                if process_clean:
                    # PHOTO -> PROC_PH, ETCH -> PROC_ET 등 매핑
                    process_map = {
                        'PHOTO': 'PROC_PH',
                        'ETCH': 'PROC_ET',
                        'CVD': 'PROC_TF',
                        'DIFFUSION': 'PROC_DF',
                        'CMP': 'PROC_CM',
                        'IMPLANT': 'PROC_IMP',
                        'CLEANING': 'PROC_CLN',
                        'METROLOGY': 'PROC_MI'
                    }
                    return process_map.get(process_clean, f'PROC_{process_clean}')
        
        return None
    
    def _extract_model_id(self, text: str) -> Optional[str]:
        """모델 ID 추출"""
        text_upper = text.upper()
        
        for pattern in self.MODEL_PATTERNS:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                model = match.group(1) if match.groups() else match.group(0)
                # MDL_ 형식인 경우 그대로 사용
                if model.startswith('MDL_'):
                    return model
                # MODEL- 형식인 경우 MODEL- 제거하고 정리
                model = re.sub(r'MODEL[-\s]*', '', model, flags=re.IGNORECASE)
                if model:
                    # MDL_KE_PRO 형식으로 변환
                    if '_' in model:
                        return model
                    # MDL-KE-PRO 형식으로 변환
                    return f"MDL_{model.replace('-', '_')}" if '-' in model else f"MDL_{model}"
        
        return None
    
    def _extract_down_type(self, text: str) -> Optional[str]:
        """다운타임 유형 추출"""
        text_upper = text.upper()
        
        for pattern, down_type in self.DOWN_TYPE_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return down_type
        
        return None
    
    def _extract_down_time(self, text: str) -> Optional[float]:
        """다운타임 시간 추출 (분 단위)"""
        # N시간 M분 패턴 먼저 처리
        time_match = re.search(r'(\d+(?:\.\d+)?)\s*시간\s*(\d+(?:\.\d+)?)\s*분', text, re.IGNORECASE)
        if time_match:
            hours = float(time_match.group(1))
            minutes = float(time_match.group(2))
            return hours * 60 + minutes
        
        # 단일 시간 단위 패턴
        for pattern, multiplier in self.TIME_PATTERNS:
            if multiplier is None:  # 이미 처리된 패턴
                continue
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                return value * multiplier
        
        return None


# 전역 인스턴스
question_analyzer = QuestionAnalyzer()

