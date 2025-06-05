"""
个性化回应验证器

对生成的角色回应进行细粒度验证，确保符合角色特性、上下文一致性和质量标准。
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from app.models import Character


class ValidationLevel(Enum):
    """验证级别枚举"""
    STRICT = "strict"       # 严格验证
    NORMAL = "normal"       # 正常验证
    LENIENT = "lenient"     # 宽松验证


class ValidationCategory(Enum):
    """验证类别枚举"""
    CHARACTER_CONSISTENCY = "character_consistency"   # 角色一致性
    LANGUAGE_STYLE = "language_style"                 # 语言风格
    EMOTIONAL_APPROPRIATENESS = "emotional_appropriateness"  # 情感适当性
    CONTENT_SAFETY = "content_safety"                 # 内容安全性
    RESPONSE_QUALITY = "response_quality"             # 回应质量
    CONTEXT_RELEVANCE = "context_relevance"           # 上下文相关性


@dataclass
class ValidationResult:
    """验证结果数据结构"""
    category: ValidationCategory
    passed: bool
    score: float  # 0-1 的分数
    issues: List[str]
    suggestions: List[str]
    severity: str  # low, medium, high, critical


@dataclass
class ResponseValidationSummary:
    """回应验证摘要"""
    overall_score: float
    overall_passed: bool
    validation_results: List[ValidationResult]
    major_issues: List[str]
    recommendations: List[str]
    requires_regeneration: bool


class ResponseValidator:
    """个性化回应验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 验证规则配置
        self.validation_rules = {
            ValidationCategory.CHARACTER_CONSISTENCY: {
                "weight": 0.25,
                "min_score": 0.7,
                "critical_threshold": 0.5
            },
            ValidationCategory.LANGUAGE_STYLE: {
                "weight": 0.20,
                "min_score": 0.6,
                "critical_threshold": 0.4
            },
            ValidationCategory.EMOTIONAL_APPROPRIATENESS: {
                "weight": 0.20,
                "min_score": 0.6,
                "critical_threshold": 0.3
            },
            ValidationCategory.CONTENT_SAFETY: {
                "weight": 0.15,
                "min_score": 0.8,
                "critical_threshold": 0.7
            },
            ValidationCategory.RESPONSE_QUALITY: {
                "weight": 0.15,
                "min_score": 0.6,
                "critical_threshold": 0.4
            },
            ValidationCategory.CONTEXT_RELEVANCE: {
                "weight": 0.05,
                "min_score": 0.5,
                "critical_threshold": 0.3
            }
        }
        
        # 问题标识符
        self.issue_patterns = {
            "out_of_character": [
                "性格不符", "角色偏离", "行为异常", "语言风格不一致"
            ],
            "inappropriate_emotion": [
                "情感不当", "情绪过度", "情感冲突", "情绪不一致"
            ],
            "poor_quality": [
                "回应质量低", "内容空洞", "逻辑不清", "表达混乱"
            ],
            "safety_concern": [
                "内容不当", "敏感信息", "安全隐患", "违规内容"
            ]
        }
    
    def validate_response(
        self,
        character: Character,
        user_message: str,
        character_response: str,
        context: Dict[str, Any],
        validation_level: ValidationLevel = ValidationLevel.NORMAL
    ) -> ResponseValidationSummary:
        """
        验证角色回应
        
        Args:
            character: 角色对象
            user_message: 用户消息
            character_response: 角色回应
            context: 上下文信息
            validation_level: 验证级别
            
        Returns:
            ResponseValidationSummary: 验证摘要
        """
        validation_results = []
        
        # 角色一致性验证
        consistency_result = self._validate_character_consistency(
            character, character_response, context
        )
        validation_results.append(consistency_result)
        
        # 语言风格验证
        style_result = self._validate_language_style(
            character, character_response, validation_level
        )
        validation_results.append(style_result)
        
        # 情感适当性验证
        emotion_result = self._validate_emotional_appropriateness(
            character, user_message, character_response, context
        )
        validation_results.append(emotion_result)
        
        # 内容安全性验证
        safety_result = self._validate_content_safety(
            character_response, validation_level
        )
        validation_results.append(safety_result)
        
        # 回应质量验证
        quality_result = self._validate_response_quality(
            user_message, character_response, context
        )
        validation_results.append(quality_result)
        
        # 上下文相关性验证
        relevance_result = self._validate_context_relevance(
            user_message, character_response, context
        )
        validation_results.append(relevance_result)
        
        # 计算总体得分
        overall_score = self._calculate_overall_score(validation_results)
        
        # 生成摘要
        summary = self._generate_validation_summary(
            validation_results, overall_score, validation_level
        )
        
        return summary
    
    def _validate_character_consistency(
        self,
        character: Character,
        response: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """验证角色一致性"""
        issues = []
        suggestions = []
        score = 1.0
        
        config_data = getattr(character, '_config_data', {})
        behavioral_constraints = config_data.get('behavioral_constraints', {})
        personality_deep = config_data.get('personality_deep', {})
        
        # 检查禁用词汇
        forbidden_words = behavioral_constraints.get('forbidden_words', [])
        for word in forbidden_words:
            if word in response:
                issues.append(f"使用了角色禁用词汇: '{word}'")
                score -= 0.2
                suggestions.append(f"移除或替换词汇 '{word}'")
        
        # 检查必须使用的表达
        preferred_expressions = behavioral_constraints.get('preferred_expressions', [])
        if preferred_expressions:
            used_preferred = any(expr in response for expr in preferred_expressions)
            if not used_preferred and len(response) > 20:  # 长回应应该包含特色表达
                issues.append("未使用角色特色表达")
                score -= 0.1
                suggestions.append(f"考虑使用: {', '.join(preferred_expressions[:3])}")
        
        # 检查核心特质体现
        core_traits = personality_deep.get('core_traits', [])
        trait_reflected = self._check_trait_reflection(response, core_traits)
        if not trait_reflected and len(response) > 30:
            issues.append("回应未体现角色核心特质")
            score -= 0.15
            suggestions.append("调整回应以更好地体现角色性格")
        
        # 检查行为约束
        must_do = behavioral_constraints.get('must_do', [])
        must_not_do = behavioral_constraints.get('must_not_do', [])
        
        constraint_violations = self._check_behavioral_constraints(
            response, must_do, must_not_do
        )
        if constraint_violations:
            issues.extend(constraint_violations)
            score -= len(constraint_violations) * 0.1
            suggestions.append("确保遵守角色行为约束")
        
        severity = self._determine_severity(score, 0.7)
        
        return ValidationResult(
            category=ValidationCategory.CHARACTER_CONSISTENCY,
            passed=score >= 0.7,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            severity=severity
        )
    
    def _validate_language_style(
        self,
        character: Character,
        response: str,
        validation_level: ValidationLevel
    ) -> ValidationResult:
        """验证语言风格"""
        issues = []
        suggestions = []
        score = 1.0
        
        config_data = getattr(character, '_config_data', {})
        language_style = config_data.get('language_style', {})
        
        # 检查语言模式
        speech_patterns = language_style.get('speech_patterns', [])
        if speech_patterns:
            pattern_match = any(
                pattern.lower() in response.lower() 
                for pattern in speech_patterns
            )
            if not pattern_match and len(response) > 15:
                issues.append("语言模式不符合角色特色")
                score -= 0.2
                suggestions.append("使用更符合角色的语言模式")
        
        # 检查语调一致性
        tone_consistency = self._check_tone_consistency(response, character)
        if tone_consistency < 0.7:
            issues.append("语调与角色不符")
            score -= (1.0 - tone_consistency) * 0.3
            suggestions.append("调整语调以匹配角色特性")
        
        # 检查正式程度
        formality_level = self._assess_formality_level(response)
        expected_formality = self._get_expected_formality(character)
        formality_diff = abs(formality_level - expected_formality)
        
        if formality_diff > 0.3:
            issues.append("正式程度与角色期待不符")
            score -= formality_diff * 0.2
            suggestions.append("调整语言的正式程度")
        
        severity = self._determine_severity(score, 0.6)
        
        return ValidationResult(
            category=ValidationCategory.LANGUAGE_STYLE,
            passed=score >= 0.6,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            severity=severity
        )
    
    def _validate_emotional_appropriateness(
        self,
        character: Character,
        user_message: str,
        response: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """验证情感适当性"""
        issues = []
        suggestions = []
        score = 1.0
        
        # 分析用户情感
        user_emotion = self._detect_message_emotion(user_message)
        response_emotion = self._detect_message_emotion(response)
        
        # 检查情感一致性
        emotion_appropriateness = self._check_emotion_appropriateness(
            user_emotion, response_emotion, character, context
        )
        
        if emotion_appropriateness < 0.6:
            issues.append("回应情感与用户情感或角色特性不匹配")
            score -= (1.0 - emotion_appropriateness) * 0.4
            suggestions.append("调整回应的情感表达")
        
        # 检查情感强度
        emotion_intensity = self._assess_emotion_intensity(response)
        if emotion_intensity > 0.8:  # 过于强烈
            config_data = getattr(character, '_config_data', {})
            personality = config_data.get('personality_deep', {})
            extraversion = personality.get('big_five_personality', {}).get('extraversion', 5)
            
            if extraversion < 5 and emotion_intensity > 0.7:  # 内向角色不应过于激动
                issues.append("情感表达过于强烈，不符合角色性格")
                score -= 0.2
                suggestions.append("降低情感表达的强度")
        
        severity = self._determine_severity(score, 0.6)
        
        return ValidationResult(
            category=ValidationCategory.EMOTIONAL_APPROPRIATENESS,
            passed=score >= 0.6,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            severity=severity
        )
    
    def _validate_content_safety(
        self,
        response: str,
        validation_level: ValidationLevel
    ) -> ValidationResult:
        """验证内容安全性"""
        issues = []
        suggestions = []
        score = 1.0
        
        # 检查不当内容
        inappropriate_patterns = [
            r'(?i)(暴力|血腥|色情)',
            r'(?i)(歧视|仇恨|攻击)',
            r'(?i)(个人信息|隐私|地址)',
            r'(?i)(违法|犯罪|危险行为)'
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, response):
                issues.append("包含潜在不当内容")
                score -= 0.3
                suggestions.append("移除不当内容")
                break
        
        # 检查敏感话题处理
        sensitive_keywords = ["政治", "宗教", "种族", "性别歧视"]
        for keyword in sensitive_keywords:
            if keyword in response:
                if validation_level == ValidationLevel.STRICT:
                    issues.append(f"涉及敏感话题: {keyword}")
                    score -= 0.2
                    suggestions.append("避免或更谨慎地处理敏感话题")
        
        # 检查年龄适宜性
        age_inappropriate = self._check_age_appropriateness(response)
        if not age_inappropriate:
            issues.append("内容可能不适合全年龄段")
            score -= 0.25
            suggestions.append("确保内容适合全年龄段用户")
        
        severity = self._determine_severity(score, 0.8)
        
        return ValidationResult(
            category=ValidationCategory.CONTENT_SAFETY,
            passed=score >= 0.8,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            severity=severity
        )
    
    def _validate_response_quality(
        self,
        user_message: str,
        response: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """验证回应质量"""
        issues = []
        suggestions = []
        score = 1.0
        
        # 检查回应长度适当性
        if len(response.strip()) < 5:
            issues.append("回应过短，缺乏内容")
            score -= 0.4
            suggestions.append("增加回应内容的丰富性")
        elif len(response) > 500:
            issues.append("回应过长，可能冗余")
            score -= 0.1
            suggestions.append("简化回应内容")
        
        # 检查重复性
        repetition_score = self._check_repetition(response)
        if repetition_score > 0.3:
            issues.append("回应内容存在重复")
            score -= repetition_score * 0.3
            suggestions.append("减少重复表达")
        
        # 检查逻辑一致性
        logical_consistency = self._check_logical_consistency(response)
        if logical_consistency < 0.7:
            issues.append("回应逻辑不够清晰")
            score -= (1.0 - logical_consistency) * 0.2
            suggestions.append("改善回应的逻辑结构")
        
        # 检查信息价值
        information_value = self._assess_information_value(user_message, response)
        if information_value < 0.5:
            issues.append("回应信息价值较低")
            score -= (1.0 - information_value) * 0.2
            suggestions.append("提供更有价值的回应内容")
        
        severity = self._determine_severity(score, 0.6)
        
        return ValidationResult(
            category=ValidationCategory.RESPONSE_QUALITY,
            passed=score >= 0.6,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            severity=severity
        )
    
    def _validate_context_relevance(
        self,
        user_message: str,
        response: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """验证上下文相关性"""
        issues = []
        suggestions = []
        score = 1.0
        
        # 检查主题相关性
        topic_relevance = self._assess_topic_relevance(user_message, response)
        if topic_relevance < 0.6:
            issues.append("回应与用户话题相关性不足")
            score -= (1.0 - topic_relevance) * 0.3
            suggestions.append("确保回应与用户话题相关")
        
        # 检查上下文连贯性
        context_coherence = self._check_context_coherence(response, context)
        if context_coherence < 0.7:
            issues.append("回应与上下文连贯性不足")
            score -= (1.0 - context_coherence) * 0.2
            suggestions.append("改善与上下文的连贯性")
        
        severity = self._determine_severity(score, 0.5)
        
        return ValidationResult(
            category=ValidationCategory.CONTEXT_RELEVANCE,
            passed=score >= 0.5,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            severity=severity
        )
    
    def _calculate_overall_score(self, validation_results: List[ValidationResult]) -> float:
        """计算总体得分"""
        weighted_score = 0.0
        total_weight = 0.0
        
        for result in validation_results:
            rule_config = self.validation_rules.get(result.category, {})
            weight = rule_config.get("weight", 0.1)
            weighted_score += result.score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_validation_summary(
        self,
        validation_results: List[ValidationResult],
        overall_score: float,
        validation_level: ValidationLevel
    ) -> ResponseValidationSummary:
        """生成验证摘要"""
        # 确定是否通过
        overall_passed = overall_score >= 0.6  # 可配置的阈值
        
        # 收集主要问题
        major_issues = []
        recommendations = []
        
        for result in validation_results:
            if result.severity in ["high", "critical"]:
                major_issues.extend(result.issues)
            recommendations.extend(result.suggestions)
        
        # 确定是否需要重新生成
        requires_regeneration = (
            overall_score < 0.4 or 
            any(r.severity == "critical" for r in validation_results) or
            not overall_passed
        )
        
        return ResponseValidationSummary(
            overall_score=overall_score,
            overall_passed=overall_passed,
            validation_results=validation_results,
            major_issues=major_issues,
            recommendations=list(set(recommendations)),  # 去重
            requires_regeneration=requires_regeneration
        )
    
    # 辅助方法
    def _check_trait_reflection(self, response: str, traits: List[str]) -> bool:
        """检查特质体现"""
        trait_indicators = {
            "冷淡": ["...", "是吗", "这样", "无所谓"],
            "活泼": ["!", "哈", "呀", "太好了"],
            "温柔": ["呢", "吧", "好的", "谢谢"],
            "强势": ["必须", "一定", "当然", "绝对"]
        }
        
        for trait in traits:
            indicators = trait_indicators.get(trait, [])
            if any(indicator in response for indicator in indicators):
                return True
        
        return False
    
    def _check_behavioral_constraints(
        self, 
        response: str, 
        must_do: List[str], 
        must_not_do: List[str]
    ) -> List[str]:
        """检查行为约束"""
        violations = []
        
        for constraint in must_not_do:
            if constraint.lower() in response.lower():
                violations.append(f"违反约束: {constraint}")
        
        # 简化的must_do检查
        if must_do and len(response) > 20:
            constraint_met = any(
                constraint.lower() in response.lower() 
                for constraint in must_do
            )
            if not constraint_met:
                violations.append("未满足必要行为约束")
        
        return violations
    
    def _determine_severity(self, score: float, threshold: float) -> str:
        """确定严重程度"""
        if score >= threshold:
            return "low"
        elif score >= threshold - 0.2:
            return "medium"
        elif score >= threshold - 0.4:
            return "high"
        else:
            return "critical"
    
    def _detect_message_emotion(self, message: str) -> str:
        """检测消息情感"""
        emotion_keywords = {
            "happy": ["开心", "高兴", "快乐", "喜欢", "好棒"],
            "sad": ["难过", "伤心", "失望", "沮丧", "不开心"],
            "angry": ["生气", "愤怒", "烦躁", "讨厌", "气死了"],
            "neutral": []
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in message for keyword in keywords):
                return emotion
        
        return "neutral"
    
    def _check_emotion_appropriateness(
        self, 
        user_emotion: str, 
        response_emotion: str, 
        character: Character, 
        context: Dict[str, Any]
    ) -> float:
        """检查情感适当性"""
        # 简化的情感适当性检查
        if user_emotion == "sad" and response_emotion in ["happy", "angry"]:
            return 0.3  # 不太合适
        elif user_emotion == "happy" and response_emotion == "angry":
            return 0.4  # 不太合适
        else:
            return 0.8  # 基本合适
    
    def _assess_emotion_intensity(self, response: str) -> float:
        """评估情感强度"""
        intensity_markers = response.count('!') + response.count('！')
        caps_ratio = sum(1 for c in response if c.isupper()) / max(1, len(response))
        
        return min(1.0, (intensity_markers * 0.2) + (caps_ratio * 2))
    
    def _check_repetition(self, response: str) -> float:
        """检查重复性"""
        words = response.split()
        if len(words) < 3:
            return 0.0
        
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        repeated_words = sum(1 for count in word_counts.values() if count > 1)
        return repeated_words / len(words)
    
    def _assess_information_value(self, user_message: str, response: str) -> float:
        """评估信息价值"""
        # 简化的信息价值评估
        response_length = len(response.strip())
        if response_length < 10:
            return 0.2
        elif response_length < 30:
            return 0.5
        else:
            return 0.8 