"""
AI新闻筛选模块 - 使用Gemini筛选优质新闻
"""
import os
import json
import time
import ssl
import urllib3
import socket
from typing import List, Dict
from google import genai
from google.genai import types

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NewsQualityFilter:
    def __init__(self, api_key=None):
        """初始化AI筛选器"""
        if not api_key:
            api_key = os.getenv('GEMINI_API_KEY')
        
        # 配置更宽松的SSL设置
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    def get_topic_system_instruction(self, category: str) -> str:
        """根据专题/分类返回更精确的系统提示"""
        topic = (category or '').strip()

        if topic == '游戏+直播':
            return (
                '你是一个专业的游戏、电竞与直播行业分析师，擅长识别对直播平台、游戏内容供给、电竞赛事、'
                '主播生态、用户时长、平台竞争、广告/打赏/电商/会员等变现模式有重要影响的新闻。'
                '请优先保留与游戏行业变化、版号政策、赛事与战队、直播平台竞争格局、流量与变现相关的内容，'
                '弱化泛科技、泛财经但与游戏或直播平台关联度较低的新闻。请严格按照JSON格式返回结果。'
            )

        if topic == '中国互联网':
            return (
                '你是一个专业的中国互联网平台分析师，擅长识别对内容平台、流量分发、广告商业化、平台竞争、'
                '监管政策、中概互联网市场情绪有重要影响的新闻。请优先保留与腾讯、字节、阿里、京东、美团、'
                '快手、B站、小红书等平台公司战略与运营变化，以及内容平台、广告营销、监管与资本市场影响相关的内容。'
                '弱化与中国互联网平台生态关联度较低的泛国际科技新闻。请严格按照JSON格式返回结果。'
            )

        return f'你是一个专业的{topic}领域新闻编辑，擅长识别和筛选高质量、有价值的新闻内容。请严格按照JSON格式返回结果。'

    def create_filtering_prompt(self, articles: List[Dict], category: str, target_count: int = 10) -> str:
        """创建筛选提示词"""
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get('title', '').strip()
            description = article.get('description', '').strip()[:150]
            articles_text += f"{i}. 【{title}】\n   内容摘要: {description}...\n\n"

        topic = (category or '').strip()

        if topic == '游戏+直播':
            prompt = f"""请作为专业的游戏、电竞与直播行业分析师，从以下{len(articles)}篇新闻中筛选出{target_count}篇最值得跟踪的新闻。

## 筛选标准 (按重要性排序):
1. **行业影响**: 对游戏、电竞、直播平台生态具有直接影响
2. **平台相关性**: 对直播平台竞争、用户时长、主播生态、内容供给有启发意义
3. **商业化价值**: 涉及广告、打赏、电商、会员、赛事商业化、平台变现模式变化
4. **政策与供给**: 与版号、监管、赛事、厂商发行、内容供给变化相关
5. **时效性与信息价值**: 信息新、变化大、值得持续跟踪

## 需要筛选的新闻:
{articles_text}

## 输出要求:
请严格按照以下JSON格式输出，不要添加任何其他文字:
{{
  "selected_numbers": [1, 3, 5, 7, 9],
  "reason": "筛选了最能反映游戏、电竞、直播平台生态变化和商业化影响的新闻"
}}

注意: selected_numbers数组中必须包含{target_count}个有效序号(1-{len(articles)})，按质量从高到低排序。"""
            return prompt

        if topic == '中国互联网':
            prompt = f"""请作为专业的中国互联网平台分析师，从以下{len(articles)}篇新闻中筛选出{target_count}篇最值得跟踪的新闻。

## 筛选标准 (按重要性排序):
1. **平台格局**: 对中国互联网平台竞争、内容分发、社区与流量格局有直接影响
2. **商业化价值**: 涉及广告、营销、电商、本地生活、会员、内容变现等关键商业模式
3. **监管与政策**: 与数据、内容合规、未成年人、平台治理等政策变化相关
4. **资本市场影响**: 对中概互联网估值、市场情绪、投资预期有参考价值
5. **时效性与信息价值**: 信息新、变化大、值得持续跟踪

## 需要筛选的新闻:
{articles_text}

## 输出要求:
请严格按照以下JSON格式输出，不要添加任何其他文字:
{{
  "selected_numbers": [1, 3, 5, 7, 9],
  "reason": "筛选了最能反映中国互联网平台竞争、商业化与监管变化的新闻"
}}

注意: selected_numbers数组中必须包含{target_count}个有效序号(1-{len(articles)})，按质量从高到低排序。"""
            return prompt
        
        prompt = f"""请作为专业的{category}领域新闻编辑，从以下{len(articles)}篇新闻中筛选出{target_count}篇最优质的新闻。

## 筛选标准 (按重要性排序):
1. **信息价值**: 提供新颖、重要的信息，具有学习或参考价值
2. **行业影响**: 对{category}领域具有重要影响或启发意义  
3. **内容质量**: 标题专业清晰，避免标题党和营销软文
4. **时效性**: 具有当下的相关性和时效性
5. **可读性**: 内容结构清晰，表达专业

## 需要筛选的新闻:
{articles_text}

## 输出要求:
请严格按照以下JSON格式输出，不要添加任何其他文字:
{{
  "selected_numbers": [1, 3, 5, 7, 9],
  "reason": "筛选了具有高信息价值和行业影响力的新闻，避免了重复内容和营销软文"
}}

注意: selected_numbers数组中必须包含{target_count}个有效序号(1-{len(articles)})，按质量从高到低排序。"""
        
        return prompt
    
    def test_network_connectivity(self):
        """测试网络连接"""
        try:
            socket.gethostbyname('generativelanguage.googleapis.com')
            sock = socket.create_connection(('generativelanguage.googleapis.com', 443), timeout=10)
            sock.close()
            print("  🌐 网络连接测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 网络连接测试失败: {e}")
            return False
    
    def call_gemini_simple(self, prompt: str, category: str) -> str:
        """简化版Gemini API调用"""
        try:
            print(f"  🔄 使用简化API调用...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"  ❌ 简化API调用失败: {e}")
            return ""
    
    def call_gemini_with_retry(self, prompt: str, category: str, max_retries: int = 3) -> str:
        """带重试机制的Gemini API调用"""
        if not self.test_network_connectivity():
            print("  ❌ 网络连接不可用，跳过AI调用")
            return ""
        
        for attempt in range(max_retries):
            try:
                print(f"  🔄 API调用尝试 {attempt + 1}/{max_retries}")
                system_instruction = self.get_topic_system_instruction(category)
                
                if attempt == 0:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.1,
                        ),
                    )
                else:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                        ),
                    )
                
                result_text = response.text.strip()
                if result_text:
                    print(f"  ✅ API调用成功")
                    return result_text
                else:
                    print(f"  ⚠️ API返回空结果")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"  ⚠️ 第{attempt + 1}次调用失败: {error_msg}")
                
                if "SSL" in error_msg or "EOF" in error_msg or "protocol" in error_msg:
                    print(f"  🌐 SSL连接问题，尝试简化调用...")
                    try:
                        simple_result = self.call_gemini_simple(prompt, category)
                        if simple_result:
                            return simple_result
                    except:
                        pass
                    
                    wait_time = (attempt + 1) * 3
                    print(f"  ⏰ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    
                elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    print(f"  🚫 配额限制，等待更长时间...")
                    time.sleep((attempt + 1) * 8)
                    
                else:
                    print(f"  ❌ 其他错误，等待后重试...")
                    time.sleep(attempt + 2)
                
                if attempt == max_retries - 1:
                    print(f"  💥 所有重试都失败了")
                    raise e
        
        return ""
    
    def filter_articles(self, articles: List[Dict], category: str, target_count: int = 10) -> List[Dict]:
        """使用AI筛选优质新闻"""
        if not articles:
            return []
        
        if len(articles) <= target_count:
            print(f"  🤖 文章数量({len(articles)})不超过目标数量({target_count})，无需筛选")
            return articles
        
        try:
            print(f"  🤖 使用AI筛选 {len(articles)} → {target_count} 篇优质新闻...")
            prompt = self.create_filtering_prompt(articles, category, target_count)
            response_text = self.call_gemini_with_retry(prompt, category, max_retries=3)
            
            if not response_text:
                print(f"  ❌ AI调用完全失败，降级为智能筛选")
                return self.intelligent_fallback_filter(articles, category, target_count)
            
            print(f"  🤖 AI响应: {response_text[:100]}...")
            
            try:
                cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
                
                if cleaned_text.startswith('{') and cleaned_text.endswith('}'):
                    result = json.loads(cleaned_text)
                else:
                    import re
                    json_match = re.search(r'\{.*?\}', cleaned_text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        raise ValueError("无法找到有效的JSON响应")
                
                selected_numbers = result.get('selected_numbers', [])
                reason = result.get('reason', '未提供筛选理由')
                
                if not isinstance(selected_numbers, list) or len(selected_numbers) == 0:
                    raise ValueError("AI返回的序号列表无效")
                
                selected_numbers = selected_numbers[:target_count]
                
                print(f"  🎯 筛选理由: {reason}")
                print(f"  📋 选中序号: {selected_numbers}")
                
                filtered_articles = []
                for num in selected_numbers:
                    if isinstance(num, int) and 1 <= num <= len(articles):
                        article = articles[num - 1]
                        filtered_articles.append(article)
                        print(f"    ✅ {num}. {article.get('title', '')[:50]}...")
                    else:
                        print(f"    ⚠️ 无效序号: {num}")
                
                if len(filtered_articles) > 0:
                    print(f"  🎉 AI筛选完成: {len(articles)} → {len(filtered_articles)} 篇")
                    return filtered_articles
                else:
                    print(f"  ⚠️ AI筛选结果为空，使用智能降级筛选")
                    return self.intelligent_fallback_filter(articles, category, target_count)
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"  ⚠️ 解析AI响应失败: {e}")
                print(f"  📝 原始响应: {response_text[:200]}...")
                print(f"  🔄 降级为智能筛选")
                return self.intelligent_fallback_filter(articles, category, target_count)
                
        except Exception as e:
            print(f"  ❌ AI筛选失败: {e}")
            print(f"  🔄 降级为智能筛选")
            return self.intelligent_fallback_filter(articles, category, target_count)
    
    def intelligent_fallback_filter(self, articles: List[Dict], category: str, target_count: int) -> List[Dict]:
        """智能降级筛选（基于关键词和规则）"""
        print(f"  🧠 使用智能规则筛选...")
        
        category_keywords = {
            'AI': ['AI', 'artificial intelligence', '人工智能', '机器学习', '深度学习', 'GPT', '神经网络', '算法', 'LLM', '大模型'],
            'Technology': ['技术', '科技', '创新', '突破', '发布', '研发', '产品', '系统', '平台', '芯片'],
            'Finance': ['金融', '投资', '股票', '市场', '经济', '银行', '资本', '融资', 'IPO', '财报'],
            '游戏+直播': ['游戏', '电竞', '直播', '主播', '赛事', '版号', '战队', '平台', '打赏', '会员', '电商'],
            '中国互联网': ['中国互联网', '平台', '腾讯', '字节', '阿里', '京东', '美团', '快手', 'b站', '小红书', '广告', '流量', '监管', '中概']
        }
        
        negative_keywords = ['广告', '推广', '营销', '促销', '优惠', '招聘', '股市行情', '今日']
        scored_articles = []
        keywords = category_keywords.get(category, [])
        
        for article in articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"
            score = 0
            
            for keyword in keywords:
                if keyword.lower() in content:
                    score += 2
            
            for neg_keyword in negative_keywords:
                if neg_keyword in content:
                    score -= 1
            
            title_len = len(article.get('title', ''))
            if 10 <= title_len <= 100:
                score += 1
            
            if article.get('description', '').strip():
                score += 1
            
            scored_articles.append((score, article))
        
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        filtered_articles = [article for score, article in scored_articles[:target_count]]
        
        print(f"  📊 智能筛选完成: {len(articles)} → {len(filtered_articles)} 篇")
        for i, (score, article) in enumerate(scored_articles[:target_count], 1):
            print(f"    🎯 {i}. (分数:{score}) {article.get('title', '')[:50]}...")
        
        return filtered_articles
    
    def batch_filter_by_category(self, articles_by_category: Dict[str, List[Dict]], target_count: int = 10) -> Dict[str, List[Dict]]:
        """批量按分类筛选"""
        filtered_results = {}
        for category, articles in articles_by_category.items():
            print(f"\n🔍 筛选分类: {category}")
            filtered_articles = self.filter_articles(articles, category, target_count)
            filtered_results[category] = filtered_articles
            time.sleep(2)
        return filtered_results

def test_ai_filter():
    """测试AI筛选功能"""
    sample_articles = [
        {"title": "AI技术突破：GPT-5发布引领新时代", "description": "OpenAI正式发布GPT-5，在推理能力和多模态理解方面实现重大突破"},
        {"title": "今日股市行情分析", "description": "股市今日上涨，投资者关注科技板块表现"},
        {"title": "人工智能在医疗诊断中的新应用", "description": "最新研究显示AI在癌症早期筛查中准确率达95%"},
        {"title": "区块链技术最新发展动态", "description": "区块链在金融科技领域的应用持续扩展"},
        {"title": "机器学习算法优化新方法", "description": "研究团队提出了一种新的神经网络训练优化算法"},
        {"title": "科技公司财报季来临", "description": "多家知名科技公司即将发布季度财报"},
        {"title": "自动驾驶技术实现新突破", "description": "特斯拉FSD系统在城市道路测试中表现优异"},
        {"title": "量子计算研究获得重要进展", "description": "IBM发布新一代量子处理器，计算能力显著提升"},
        {"title": "AI芯片市场竞争加剧", "description": "英伟达、AMD等公司在AI芯片领域展开激烈竞争"},
        {"title": "元宇宙概念股集体上涨", "description": "投资者对元宇宙技术发展前景保持乐观"},
        {"title": "深度学习在图像识别中的应用", "description": "新的深度学习模型在图像分类任务中达到人类水平"},
        {"title": "5G网络建设加速推进", "description": "全球5G基站部署数量持续增长，覆盖范围不断扩大"}
    ]
    
    print("🧪 开始测试AI筛选功能...")
    filter_instance = NewsQualityFilter()
    filtered = filter_instance.filter_articles(sample_articles, category="AI", target_count=5)
    
    print(f"\n📊 筛选结果 ({len(filtered)} 篇):")
    for i, article in enumerate(filtered, 1):
        print(f"{i}. {article['title']}")

if __name__ == "__main__":
    test_ai_filter()
