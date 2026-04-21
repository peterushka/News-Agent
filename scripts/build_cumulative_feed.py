"""
累积RSS Feed生成脚本

基于累积新闻文档生成RSS Feed，支持增量更新和严格去重
"""

import os
import sys
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from news_agent.config_loader import get_project_paths, load_config
from news_agent.history.rss_history import RSSHistoryManager
from news_agent.utils.deduplicate import create_content_fingerprint, calculate_title_similarity
from news_agent.rss.feed_generator import generate_rss_xml, read_existing_rss_metadata, get_rss_filename

try:
    from news_agent.filters.ai_news_filter import NewsQualityFilter
    AI_FILTER_AVAILABLE = True
except ImportError:
    print("⚠️ AI筛选模块不可用，将跳过AI筛选功能")
    AI_FILTER_AVAILABLE = False

TOPIC_CHANNELS = {
    '游戏+直播': {
        'keywords': ['游戏', '电竞', '直播', '主播', '赛事', '版号', '战队', 'game', 'gaming', 'esports', 'livestream', 'streaming']
    },
    '中国互联网': {
        'keywords': ['中国互联网', '腾讯', '字节', '阿里', '京东', '美团', '快手', 'b站', '小红书', '平台', '广告', '流量', '监管', '中概', 'china internet', 'china tech', 'platform']
    }
}


def parse_cumulative_markdown(md_file_path: str, category: str,
                             history_manager: RSSHistoryManager,
                             max_recent_articles: int = 50,
                             time_window_hours: int = 72,
                             enable_ai_filter: bool = True,
                             ai_filter_count: int = 5) -> Dict:
    """
    解析累积Markdown文件并提取文章
    """
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ❌ 读取文件失败: {e}")
        return {}

    info = {
        'title': '',
        'description': '',
        'pub_date': '',
        'articles': []
    }

    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    if title_match:
        info['title'] = title_match.group(1).strip()

    time_match = re.search(r'\*\*最后更新时间\*\*:\s*(.+)', content)
    if time_match:
        time_str = time_match.group(1).strip()
        try:
            pub_date = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            info['pub_date'] = pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
        except ValueError:
            info['pub_date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    else:
        info['pub_date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')

    info['description'] = f"{category} 分类最新新闻，增量更新确保内容新鲜"

    extraction_limit = max_recent_articles * 10
    article_pattern = r'#### \[(.+?)\]\((.+?)\)\s*(?:\*\*发布时间\*\*:\s*(.+?)(?:\n|$))?'
    articles = re.findall(article_pattern, content, re.MULTILINE | re.DOTALL)
    articles = articles[:extraction_limit]

    raw_articles = []
    time_cutoff = datetime.now() - timedelta(hours=time_window_hours)
    last_update_time = history_manager.get_last_update_time(category)

    for title, link, pub_time in articles:
        try:
            title_clean = title.replace('\\[', '[').replace('\\]', ']').strip()
            link_clean = link.strip()

            pub_datetime = None
            if pub_time:
                try:
                    pub_datetime = datetime.strptime(pub_time.strip(), '%Y-%m-%d %H:%M')
                except:
                    pass

            if pub_datetime:
                if pub_datetime < time_cutoff:
                    continue
                if last_update_time and pub_datetime <= last_update_time:
                    continue

            fingerprint = create_content_fingerprint(title_clean, link_clean)

            if history_manager.is_article_published(category, fingerprint):
                continue

            article_info = {
                'title': title_clean,
                'link': link_clean,
                'pub_date': pub_datetime.strftime('%a, %d %b %Y %H:%M:%S GMT') if pub_datetime else info['pub_date'],
                'description': title_clean,
                'fingerprint': fingerprint,
                'source_category': category,
            }

            raw_articles.append(article_info)

        except Exception as e:
            print(f"  ⚠️ 解析文章失败: {e}")
            continue

    deduplicated = []
    for article in raw_articles:
        is_duplicate = False
        for existing in deduplicated:
            similarity = calculate_title_similarity(article['title'], existing['title'])
            if similarity > 0.85:
                is_duplicate = True
                break
        if not is_duplicate:
            deduplicated.append(article)

    print(f"  📊 提取 {len(raw_articles)} 篇新文章，去重后 {len(deduplicated)} 篇")

    if enable_ai_filter and AI_FILTER_AVAILABLE and len(deduplicated) > ai_filter_count:
        print(f"  🤖 启动AI筛选: {len(deduplicated)} → {ai_filter_count} 篇")
        try:
            filter_instance = NewsQualityFilter()
            deduplicated = filter_instance.filter_articles(deduplicated, category, ai_filter_count)
        except Exception as e:
            print(f"  ⚠️ AI筛选失败: {e}")

    deduplicated = deduplicated[:max_recent_articles]
    info['articles'] = deduplicated
    return info


def process_category(category: str, cumulative_file: Path,
                    output_dir: Path, history_manager: RSSHistoryManager,
                    config: Dict) -> Dict:
    print(f"\n📰 处理分类: {category}")
    print(f"  📄 累积文件: {cumulative_file.name}")

    settings = config['settings']
    news_info = parse_cumulative_markdown(
        str(cumulative_file),
        category,
        history_manager,
        max_recent_articles=settings.get('max_articles_per_source', 50),
        time_window_hours=settings.get('time_window_hours', 72),
        enable_ai_filter=settings.get('ai_filter_enabled', True),
        ai_filter_count=settings.get('ai_filter_count', 5)
    )

    if not news_info or not news_info.get('articles'):
        print(f"  ⚠️ 没有新文章，跳过")
        return {'success': False, 'reason': '没有新文章'}

    rss_filename = get_rss_filename(category)
    rss_file_path = output_dir / rss_filename
    existing_metadata = read_existing_rss_metadata(str(rss_file_path))

    base_url = os.getenv('NEWS_AGENT_BASE_URL', 'https://peterushka.github.io/News-Agent')
    xml_content = generate_rss_xml(
        news_info,
        category,
        base_url=base_url,
        existing_metadata=existing_metadata
    )

    with open(rss_file_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    for article in news_info['articles']:
        history_manager.add_published_article(category, article['fingerprint'], article)

    history_manager.update_last_update_time(category)
    history_manager.save_history()

    print(f"  ✅ 成功生成RSS: {rss_filename}")
    print(f"  📊 包含 {len(news_info['articles'])} 篇新文章")

    return {'success': True, 'file': rss_filename, 'article_count': len(news_info['articles'])}


def build_topic_channel(topic_name: str, all_category_articles: List[Dict], output_dir: Path,
                        history_manager: RSSHistoryManager, config: Dict) -> Dict:
    print(f"\n🏷️ 处理专题频道: {topic_name}")
    rule = TOPIC_CHANNELS.get(topic_name)
    if not rule:
        return {'success': False, 'reason': '未知专题'}

    keywords = [k.lower() for k in rule.get('keywords', [])]
    matched = []
    for article in all_category_articles:
        text = f"{article.get('title', '')} {article.get('description', '')} {article.get('source_category', '')}".lower()
        if any(k in text for k in keywords):
            matched.append(dict(article))

    deduplicated = []
    for article in matched:
        is_duplicate = False
        for existing in deduplicated:
            similarity = calculate_title_similarity(article['title'], existing['title'])
            if similarity > 0.85:
                is_duplicate = True
                break
        if not is_duplicate:
            deduplicated.append(article)

    settings = config['settings']
    ai_filter_count = settings.get('ai_filter_count', 5)
    max_recent_articles = settings.get('max_articles_per_source', 50)

    if config['settings'].get('ai_filter_enabled', True) and AI_FILTER_AVAILABLE and len(deduplicated) > ai_filter_count:
        print(f"  🤖 启动专题AI筛选: {len(deduplicated)} → {ai_filter_count} 篇")
        try:
            filter_instance = NewsQualityFilter()
            deduplicated = filter_instance.filter_articles(deduplicated, topic_name, ai_filter_count)
        except Exception as e:
            print(f"  ⚠️ 专题AI筛选失败: {e}")

    deduplicated = deduplicated[:max_recent_articles]
    if not deduplicated:
        print(f"  ⚠️ 专题暂无匹配文章，跳过")
        return {'success': False, 'reason': '暂无匹配文章'}

    news_info = {
        'title': f'{topic_name} 新闻汇总',
        'description': f'{topic_name} 专题新闻聚合，由 News Agent 自动生成',
        'pub_date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'articles': deduplicated
    }

    rss_filename = get_rss_filename(topic_name)
    rss_file_path = output_dir / rss_filename
    existing_metadata = read_existing_rss_metadata(str(rss_file_path))
    base_url = os.getenv('NEWS_AGENT_BASE_URL', 'https://peterushka.github.io/News-Agent')
    xml_content = generate_rss_xml(news_info, topic_name, base_url=base_url, existing_metadata=existing_metadata)

    with open(rss_file_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    for article in deduplicated:
        history_manager.add_published_article(topic_name, article['fingerprint'], article)

    history_manager.update_last_update_time(topic_name)
    history_manager.save_history()

    print(f"  ✅ 成功生成专题RSS: {rss_filename}")
    print(f"  📊 包含 {len(deduplicated)} 篇文章")
    return {'success': True, 'file': rss_filename, 'article_count': len(deduplicated)}


def main():
    parser = argparse.ArgumentParser(description='生成累积RSS Feed')
    parser.add_argument('--category', type=str, help='指定分类（不指定则处理所有）')
    parser.add_argument('--no-ai-filter', action='store_true', help='禁用AI筛选')
    parser.add_argument('--cleanup-days', type=int, default=30, help='清理多少天前的历史记录')
    args = parser.parse_args()

    print("=" * 60)
    print("📡 累积RSS Feed生成器")
    print("=" * 60)

    config = load_config()
    paths = config['paths']
    if args.no_ai_filter:
        config['settings']['ai_filter_enabled'] = False

    print(f"\n📁 输出目录: {paths['feed']}")
    print(f"📚 累积新闻目录: {paths['cumulative_news']}")

    history_manager = RSSHistoryManager()
    print(f"\n🧹 清理 {args.cleanup_days} 天前的历史记录...")
    history_manager.cleanup_old_records(days=args.cleanup_days)

    cumulative_dir = Path(paths['cumulative_news'])
    if not cumulative_dir.exists():
        print(f"❌ 累积新闻目录不存在: {cumulative_dir}")
        return
    cumulative_files = list(cumulative_dir.glob('*_cumulative.md'))
    if not cumulative_files:
        print("❌ 没有找到累积新闻文件")
        return

    print(f"\n📂 发现 {len(cumulative_files)} 个累积新闻文件")
    results = {}
    all_category_articles = []

    for file_path in cumulative_files:
        category = file_path.stem.replace('_cumulative', '').replace('_', ' ').title()
        if args.category and category.lower() != args.category.lower():
            continue

        results[category] = process_category(category, file_path, Path(paths['feed']), history_manager, config)

        parsed_info = parse_cumulative_markdown(
            str(file_path),
            category,
            history_manager,
            max_recent_articles=config['settings'].get('max_articles_per_source', 50),
            time_window_hours=config['settings'].get('time_window_hours', 72),
            enable_ai_filter=False,
            ai_filter_count=config['settings'].get('ai_filter_count', 5)
        )
        all_category_articles.extend(parsed_info.get('articles', []))

    if not args.category:
        for topic_name in TOPIC_CHANNELS.keys():
            results[topic_name] = build_topic_channel(topic_name, all_category_articles, Path(paths['feed']), history_manager, config)

    print("\n" + "=" * 60)
    print("📊 生成统计:")
    print("=" * 60)
    successful = [cat for cat, res in results.items() if res.get('success')]
    total_articles = sum(res.get('article_count', 0) for res in results.values())
    print(f"✅ 成功: {len(successful)}/{len(results)} 个分类/专题")
    print(f"📰 总文章数: {total_articles}")
    for category, result in results.items():
        if result.get('success'):
            print(f"  ✓ {category}: {result['article_count']} 篇")
        else:
            print(f"  ✗ {category}: {result.get('reason', '失败')}")
    print(f"\n🎉 RSS Feed生成完成！")


if __name__ == "__main__":
    main()
