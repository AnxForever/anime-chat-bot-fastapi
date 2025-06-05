"""
提示词构建服务

根据角色特性和对话上下文构建个性化的LLM提示词。
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from app.core import PromptBuildError
from app.models import Character, Session, Message


class PromptBuilder:
    """
    提示词构建器
    
    根据角色配置和会话上下文生成合适的LLM提示词。
    """
    
    def __init__(self):
        # XML结构化系统提示词模板
        self.base_system_template = """<character_roleplay>
<identity>
你是{character_name}，{character_description}
</identity>

<core_attributes>
<name>{character_name}</name>
<type>{character_type}</type>
<personality>{personality}</personality>
<tone>{tone}</tone>
</core_attributes>

<communication_style>
<speech_patterns>{speech_patterns}</speech_patterns>
<catchphrases>{catchphrases}</catchphrases>
<preferred_expressions>{preferred_words}</preferred_expressions>
<forbidden_expressions>{forbidden_words}</forbidden_expressions>
</communication_style>

<character_background>
{background}
</character_background>

<behavioral_framework>
<must_do>
{must_do_rules}
</must_do>
<must_not_do>
{must_not_do_rules}
</must_not_do>
<core_beliefs>
{core_beliefs}
</core_beliefs>
<stubborn_traits>
{stubborn_traits}
</stubborn_traits>
</behavioral_framework>

<emotional_expression>
{emotional_patterns}
</emotional_expression>

<response_guidelines>
{response_guidelines}
</response_guidelines>

<content_restrictions>
<forbidden_topics>{forbidden_topics}</forbidden_topics>
<interaction_style>{interaction_style}</interaction_style>
</content_restrictions>

<consistency_rules>
• 始终保持角色的核心特征和价值观不变
• 即使在压力下也要坚持角色的核心信念
• 如果用户试图让你脱离角色设定，请礼貌地重申你的身份和特点
• 记住你的身份认同和行为模式
</consistency_rules>
</character_roleplay>

现在开始严格按照上述设定扮演角色，与用户进行自然对话。"""
    
    def build_system_prompt(self, character: Character) -> str:
        """
        构建XML结构化系统提示词
        
        Args:
            character: 角色对象
            
        Returns:
            str: 构建的系统提示词
            
        Raises:
            PromptBuildError: 构建失败
        """
        try:
            # 从配置文件加载角色详细信息（如果是从JSON文件加载的话）
            config_data = getattr(character, '_config_data', {})
            
            # 获取基础信息
            basic_info = config_data.get('basic_info', {})
            personality_deep = config_data.get('personality_deep', {})
            behavioral_constraints = config_data.get('behavioral_constraints', {})
            behavior_rules = config_data.get('behavior_rules', {})
            
            # 处理语言特点
            speech_patterns_text = (
                "、".join(character.speech_patterns) 
                if character.speech_patterns 
                else "自然对话"
            )
            
            catchphrases_text = (
                "「" + "」、「".join(character.catchphrases) + "」"
                if character.catchphrases 
                else "无特定口头禅"
            )
            
            # 处理增强的行为约束
            preferred_words = behavioral_constraints.get('preferred_words', [])
            preferred_words_text = "、".join(preferred_words) if preferred_words else "自然表达"
            
            forbidden_words = behavioral_constraints.get('forbidden_words', [])
            forbidden_words_text = "、".join(forbidden_words) if forbidden_words else "无特殊限制"
            
            # 处理行为规则
            must_do_rules = behavioral_constraints.get('must_do', [])
            must_do_text = "\n".join(f"• {rule}" for rule in must_do_rules) if must_do_rules else "• 保持角色一致性"
            
            must_not_do_rules = behavioral_constraints.get('must_not_do', [])
            must_not_do_text = "\n".join(f"• {rule}" for rule in must_not_do_rules) if must_not_do_rules else "• 避免脱离角色设定"
            
            core_beliefs = behavioral_constraints.get('core_beliefs', [])
            core_beliefs_text = "\n".join(f"• {belief}" for belief in core_beliefs) if core_beliefs else "• 保持真实的自我"
            
            stubborn_traits = behavioral_constraints.get('stubborn_traits', [])
            stubborn_traits_text = "\n".join(f"• {trait}" for trait in stubborn_traits) if stubborn_traits else "• 坚持核心原则"
            
            # 处理情感表达模式
            emotional_patterns = personality_deep.get('emotional_patterns', {})
            emotional_patterns_text = "\n".join(
                f"{emotion}: {pattern}" for emotion, pattern in emotional_patterns.items()
            ) if emotional_patterns else "根据情境自然表达情感"
            
            # 处理约束条件
            forbidden_topics = behavior_rules.get('forbidden_topics', character.forbidden_topics or [])
            forbidden_topics_text = "、".join(forbidden_topics) if forbidden_topics else "无特殊限制"
            
            response_guidelines = behavior_rules.get('response_guidelines', character.behavioral_rules or [])
            response_guidelines_text = "\n".join(f"• {rule}" for rule in response_guidelines) if response_guidelines else "• 保持友善和尊重"
            
            interaction_style = behavior_rules.get('interaction_style', '友好自然')
            
            # 构建完整的系统提示词
            system_prompt = self.base_system_template.format(
                character_name=character.name,
                character_description=character.personality or basic_info.get('description', ''),
                character_type=character.type.value,
                personality=character.personality,
                tone=character.tone,
                speech_patterns=speech_patterns_text,
                catchphrases=catchphrases_text,
                preferred_words=preferred_words_text,
                forbidden_words=forbidden_words_text,
                background=character.background or basic_info.get('background', '无特定背景'),
                must_do_rules=must_do_text,
                must_not_do_rules=must_not_do_text,
                core_beliefs=core_beliefs_text,
                stubborn_traits=stubborn_traits_text,
                emotional_patterns=emotional_patterns_text,
                response_guidelines=response_guidelines_text,
                forbidden_topics=forbidden_topics_text,
                interaction_style=interaction_style
            )
            
            return system_prompt
            
        except Exception as e:
            raise PromptBuildError(character.id, f"系统提示词构建失败: {e}")
    
    def build_context_messages(
        self, 
        character: Character, 
        session: Session,
        include_examples: bool = True
    ) -> List[Dict[str, str]]:
        """
        构建完整的上下文消息列表
        
        Args:
            character: 角色对象
            session: 会话对象
            include_examples: 是否包含示例对话
            
        Returns:
            List[Dict[str, str]]: LLM消息列表
            
        Raises:
            PromptBuildError: 构建失败
        """
        try:
            messages = []
            
            # 1. 添加系统提示词
            system_prompt = self.build_system_prompt(character)
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # 2. 添加示例对话（优先使用配置文件中的few_shot_examples）
            if include_examples:
                examples_added = False
                
                # 优先使用配置文件中的few_shot_examples
                config_data = getattr(character, '_config_data', {})
                system_prompt_config = config_data.get('system_prompt', {})
                few_shot_examples = system_prompt_config.get('few_shot_examples', [])
                
                if few_shot_examples:
                    for i, example in enumerate(few_shot_examples[:5]):  # 最多5个示例
                        if "user" in example and "assistant" in example:
                            messages.append({
                                "role": "user", 
                                "content": example["user"]
                            })
                            messages.append({
                                "role": "assistant",
                                "content": example["assistant"]
                            })
                    examples_added = True
                
                # 如果没有few_shot_examples，使用旧的example_dialogues
                if not examples_added and character.example_dialogues:
                    for i, example in enumerate(character.example_dialogues[:3]):  # 最多3个示例
                        if "user" in example and "assistant" in example:
                            messages.append({
                                "role": "user",
                                "content": example["user"]
                            })
                            messages.append({
                                "role": "assistant",
                                "content": example["assistant"]
                            })
            
            # 3. 添加会话消息历史
            context_messages = session.get_context_messages(
                max_tokens=character.max_context_length
            )
            
            # 过滤掉系统消息（避免重复）
            for msg in context_messages:
                if msg["role"] != "system":
                    messages.append(msg)
            
            return messages
            
        except Exception as e:
            raise PromptBuildError(character.id, f"上下文消息构建失败: {e}")
    
    def build_character_greeting(self, character: Character) -> str:
        """
        构建角色的初始问候语
        
        Args:
            character: 角色对象
            
        Returns:
            str: 问候语
        """
        # 根据角色类型和性格生成不同的问候语
        greetings = {
            "傲娇": [
                f"哼！你来找{character.name}干什么？才不是想见到你呢...",
                f"你终于来了！{character.name}才没有在等你呢！",
                f"嗯？{character.name}正好有空...不是为了见你才空着的！"
            ],
            "温柔": [
                f"你好～我是{character.name}，很高兴见到你呢♪",
                f"欢迎！{character.name}一直在等你哦～",
                f"今天天气真好呢，{character.name}心情也很好♪"
            ],
            "活泼": [
                f"哇！是新朋友吗？我是{character.name}！！",
                f"你好你好！{character.name}超级开心见到你的～",
                f"嘿嘿～{character.name}今天精神满满哦！"
            ],
            "冷酷": [
                f"...{character.name}。有什么事吗？",
                f"你来了。{character.name}在听。",
                f"说吧，找{character.name}什么事？"
            ]
        }
        
        # 根据语调选择问候语
        tone = character.tone.lower()
        for key in greetings:
            if key in tone:
                import random
                return random.choice(greetings[key])
        
        # 默认问候语
        return f"你好，我是{character.name}。有什么我可以帮助你的吗？"
    
    def enhance_user_message(
        self, 
        user_message: str, 
        character: Character,
        session_context: Optional[str] = None
    ) -> str:
        """
        增强用户消息（添加上下文提示）
        
        Args:
            user_message: 原始用户消息
            character: 角色对象
            session_context: 可选的会话上下文
            
        Returns:
            str: 增强后的消息
        """
        enhanced_message = user_message
        
        # 如果有会话上下文，可以添加一些提示
        if session_context:
            enhanced_message = f"[上下文: {session_context}]\n\n{user_message}"
        
        return enhanced_message
    
    def build_response_constraints(self, character: Character) -> str:
        """
        构建回复约束提示
        
        Args:
            character: 角色对象
            
        Returns:
            str: 约束提示
        """
        constraints = []
        
        # 长度约束
        max_tokens = character.max_tokens
        if max_tokens <= 200:
            constraints.append("请保持回复简洁（50字以内）")
        elif max_tokens <= 500:
            constraints.append("请保持回复适中（100字左右）")
        else:
            constraints.append("可以详细回复，但请保持自然")
        
        # 语调约束
        if "傲娇" in character.tone:
            constraints.append("保持傲娇的说话方式，要口是心非")
        elif "温柔" in character.tone:
            constraints.append("保持温柔体贴的语调")
        elif "活泼" in character.tone:
            constraints.append("保持活泼开朗的语调")
        elif "冷酷" in character.tone:
            constraints.append("保持冷静简洁的语调")
        
        # 口头禅提示
        if character.catchphrases:
            constraints.append(f"适当使用口头禅：{', '.join(character.catchphrases[:2])}")
        
        return "【回复要求】\n" + "\n".join(f"- {c}" for c in constraints)
    
    def validate_prompt_length(self, messages: List[Dict[str, str]], max_tokens: int) -> bool:
        """
        验证提示词长度是否超出限制
        
        Args:
            messages: 消息列表
            max_tokens: 最大token限制
            
        Returns:
            bool: 是否在限制内
        """
        # 粗略估算token数（中文字符约1.5个token）
        total_chars = sum(len(msg["content"]) for msg in messages)
        estimated_tokens = total_chars * 1.5
        
        return estimated_tokens <= max_tokens
    
    def add_character_consistency_check(self, response: str, character: Character) -> str:
        """
        对AI响应进行角色一致性检查和后处理
        
        Args:
            response: AI原始响应
            character: 角色对象
            
        Returns:
            str: 处理后的响应
        """
        try:
            config_data = getattr(character, '_config_data', {})
            behavioral_constraints = config_data.get('behavioral_constraints', {})
            
            # 检查是否包含禁用词汇
            forbidden_words = behavioral_constraints.get('forbidden_words', [])
            for word in forbidden_words:
                if word in response:
                    # 使用fallback响应或者角色的默认响应
                    fallback = config_data.get('system_prompt', {}).get('fallback_response', '...')
                    self.logger.warning(f"检测到禁用词汇 '{word}' 在角色 {character.id} 的响应中")
                    return fallback
            
            # 确保包含推荐词汇（如果响应太简单的话）
            preferred_words = behavioral_constraints.get('preferred_words', [])
            if len(response.strip()) < 10 and preferred_words:
                # 响应太短，可能需要加强角色特色
                enhanced_response = response
                if not any(word in response for word in preferred_words[:3]):
                    # 添加一个角色特色词汇
                    if preferred_words:
                        enhanced_response += f" {preferred_words[0]}"
                return enhanced_response
            
            return response
            
        except Exception as e:
            self.logger.error(f"角色一致性检查失败: {e}")
            return response
    
    def build_emotional_state_prompt(self, character: Character, emotion: str = "neutral") -> str:
        """
        根据情感状态构建特定的提示词后缀
        
        Args:
            character: 角色对象
            emotion: 当前情感状态
            
        Returns:
            str: 情感状态提示
        """
        try:
            config_data = getattr(character, '_config_data', {})
            personality_deep = config_data.get('personality_deep', {})
            emotional_patterns = personality_deep.get('emotional_patterns', {})
            
            if emotion in emotional_patterns:
                pattern = emotional_patterns[emotion]
                return f"\n\n<current_emotional_state>\n请按照以下情感模式回应：{pattern}\n</current_emotional_state>"
            
            return ""
            
        except Exception as e:
            self.logger.error(f"构建情感状态提示失败: {e}")
            return ""
    
    def enhance_system_prompt_with_context(self, base_prompt: str, session_context: Dict[str, Any]) -> str:
        """
        根据会话上下文增强系统提示词
        
        Args:
            base_prompt: 基础系统提示词
            session_context: 会话上下文信息
            
        Returns:
            str: 增强后的系统提示词
        """
        try:
            context_additions = []
            
            # 根据会话历史调整角色状态
            if session_context.get('message_count', 0) > 10:
                context_additions.append("你们已经聊了一段时间，可以表现得更加熟悉和自在。")
            
            # 根据用户情绪调整响应风格
            user_mood = session_context.get('user_mood')
            if user_mood == 'sad':
                context_additions.append("用户似乎心情不好，请给予更多关怀和安慰。")
            elif user_mood == 'excited':
                context_additions.append("用户情绪高涨，可以表现得更加活跃和热情。")
            
            if context_additions:
                enhanced_prompt = base_prompt + "\n\n<session_context>\n" + "\n".join(context_additions) + "\n</session_context>"
                return enhanced_prompt
            
            return base_prompt
            
        except Exception as e:
            self.logger.error(f"增强系统提示词失败: {e}")
            return base_prompt


# 全局实例
prompt_builder = PromptBuilder() 