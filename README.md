# News-Agent

新闻聚合 Agent，基于 RSS 配置抓取与聚合多语言资讯源。

## 当前状态（2026-04-21）

项目已经完成一轮可用性修复，当前主线状态如下：

### 1. 已完成的事项

- 已补充并切换为一套 **混合 RSS 策略**：
  - 原生可用源保留
  - 中文商业/科技/投资类内容优先补充 **BestBlogs / wechat2rss** 转换源
- 已合并中文商业/科技源扩充到 `main`
- 已新增并修复 GitHub Pages 部署流程
- 已将首页改为 **直接读取仓库内生成的 RSS 文件**，而不是静态展示壳
- 已修复 RSS 生成脚本中的旧域名问题：
  - 生成器默认 `base_url` 已改为 `https://peterushka.github.io/News-Agent`
  - 同时支持通过环境变量 `NEWS_AGENT_BASE_URL` 覆盖
- 已升级手动重建 workflow，可手动触发完整 RSS 重建与 Pages 部署
- 已继续补充一组 **与 DOYU / HUYA 高相关的中英文新闻源**
- 已在源配置中增加 `tags` 字段
- 已在前端首页增加两个扩展频道：`游戏+直播`、`中国互联网`
- 已确认当前 Markdown 生成不是 LLM 生成，而是 RSS 解析 + Python 模板拼接
- 已确认当前 AI 筛选模型为 **Gemini 2.5 Flash**（`gemini-2.5-flash`）

### 2. 当前线上入口

- GitHub Pages 首页：
  - `https://peterushka.github.io/News-Agent/`
- RSS 文件：
  - `https://peterushka.github.io/News-Agent/outputs/feed/aifreenewsagent.xml`
  - `https://peterushka.github.io/News-Agent/outputs/feed/technologyfreenewsagent.xml`
  - `https://peterushka.github.io/News-Agent/outputs/feed/financefreenewsagent.xml`

### 3. 当前验证结果

已确认：
- Pages 已成功发布
- 首页已切换到新版可读 RSS 的前端
- AI / Technology / Finance 三个 RSS 当前都可以访问
- AI feed 已从之前的误覆盖占位内容中恢复
- Technology / Finance feed 已重新生成并切换为 GitHub Pages 域名
- 首页文案和频道说明已更新，已包含 `游戏+直播`、`中国互联网`

### 4. DOYU / HUYA 高相关源扩充（2026-04-21）

本轮新增方向偏向：
- 游戏 / 电竞 / 直播 / 中国互联网平台
- 中概 / 平台商业化 / 广告与流量
- 英文行业媒体（游戏、电竞、广告、市场）

#### 已加入配置且当前检测可连通的高相关源

**中文 / 中文转换源**
- 白鲸出海
- 晚点 LatePost
- 暗涌 Waves
- 腾讯科技
- 网易科技
- 深网腾讯新闻

**英文**
- MarketWatch
- VentureBeat
- GamesIndustry.biz
- PocketGamer.biz
- Esports Insider
- Digiday
- Adweek

#### 已评估但暂未纳入“可用优先”集合的源

这些源在检测中表现为超时、500、证书异常或域名问题，后续如需可继续复测：
- 游戏日报（BestBlogs）
- 竞核（BestBlogs）
- 华尔街见闻（候选 RSSHub）
- 第一财经周刊（历史候选）
- 证券时报（候选）
- Financial Times
- Reuters Business
- Reuters Technology
- The Esports Advocate
- Rest of World

### 5. 标签体系（新增）

当前在 `config/rss_feed_urls.json` 中已增加 `tags` 字段，先引入两个业务导向标签：

- `游戏+直播`
- `中国互联网`

#### 当前打标示例

**游戏+直播**
- GamesIndustry.biz
- PocketGamer.biz
- Esports Insider
- 游戏日报（candidate）
- 竞核（candidate）

**中国互联网**
- 量子位
- InfoQ 中文网
- 钛媒体
- 少数派
- 机器之心
- 极客公园
- 晚点 LatePost
- 创业邦
- 42章经
- 甲子光年
- 白鲸出海
- 硅星人 Pro
- 吴晓波频道
- 刘润
- 经纬创投
- 暗涌 Waves
- 有新 Newin
- 网易科技
- 腾讯科技
- 深网腾讯新闻
- Digiday
- Adweek

### 6. 前端频道说明（新增）

首页目前包含 5 个频道：
- AI
- Technology
- Finance
- 游戏+直播
- 中国互联网

其中：
- AI / Technology / Finance：直接读取对应 RSS 文件
- 游戏+直播 / 中国互联网：当前为 **前端基于已有 RSS 的关键词聚合频道**

说明：
- 这是一种“最小可用实现”，优点是上线快、不改后端结构
- 后续更理想的做法是：生成链路把 source metadata/tag 一起写入产物，再由前端按真实 tag 渲染

### 7. AI 筛选现状（新增）

当前 AI 筛选位于：
- `news_agent/filters/ai_news_filter.py`

已确认：
- 当前模型：`gemini-2.5-flash`
- API Key 来源：`GEMINI_API_KEY`
- 用途：**新闻筛选**，不是 Markdown 生成
- 当前逻辑：
  - 给模型文章标题 + 短摘要
  - 让模型返回要保留的文章序号列表（JSON）
  - 程序再按序号筛出文章
- 如果 Gemini 调用失败：
  - 自动降级为规则筛选（关键词 / 负面词 / 标题长度 / 描述存在性）

### 8. DOYU / HUYA 专题 prompt 设计（新增）

当前 AI 筛选按大类 `AI / Technology / Finance` 工作，但对于 DOYU / HUYA 跟踪场景不够精准。
建议新增两套专题筛选 prompt：

#### A. `游戏+直播` 专题筛选 prompt

适用目标：
- 斗鱼 / 虎牙 / 直播平台生态跟踪
- 游戏内容供给
- 电竞赛事与主播生态
- 游戏行业政策与版号变化

建议筛选优先级：
1. 游戏行业重大变化（版号、头部厂商、发行、渠道）
2. 电竞赛事、战队、联赛、主播生态
3. 直播平台竞争格局、用户时长、内容供给
4. 广告、打赏、电商、会员等变现模式变化
5. 与平台流量、社区活跃度、内容消费趋势相关的新闻

建议 prompt 核心口径：
> 请作为游戏、电竞与直播行业分析师，从候选新闻中筛选出最值得跟踪的平台级新闻。优先保留对直播平台竞争、用户时长、主播生态、电竞赛事、游戏内容供给、版号政策、变现模式（广告/打赏/电商/会员）有直接影响的内容。避免保留泛科技、泛财经但与游戏或直播平台关联度低的新闻。

#### B. `中国互联网` 专题筛选 prompt

适用目标：
- 中国互联网平台格局跟踪
- 内容平台 / 广告 / 流量 / 中概情绪
- 与斗鱼 / 虎牙所处平台环境强相关的信息

建议筛选优先级：
1. 中国互联网平台竞争格局变化
2. 流量分发、内容平台、广告营销、社区产品变化
3. 腾讯、字节、阿里、京东、美团、快手、B站、小红书等平台公司的战略与运营变化
4. 监管、数据、内容合规、未成年人政策
5. 中概互联网估值、情绪、资本市场影响

建议 prompt 核心口径：
> 请作为中国互联网平台分析师，从候选新闻中筛选出最值得跟踪的平台级新闻。优先保留对内容平台、流量分发、广告商业化、平台竞争、监管政策、中概互联网市场情绪有直接影响的内容。弱化与中国互联网平台生态关联度较低的泛国际科技新闻。

### 9. 最小接入方案（新增）

为了不破坏现有 `AI / Technology / Finance` 逻辑，建议采用“最小改动接入”方案：

#### 方案目标
- 保留原有 `category` 驱动流程
- 在 `ai_news_filter.py` 内新增“专题 prompt 路由”
- 让 `游戏+直播` / `中国互联网` 可以复用现有 Gemini 调用和 JSON 解析框架

#### 最小改法
1. 在 `NewsQualityFilter` 中新增一个 prompt builder/router
   - 例如：`create_filtering_prompt_by_topic(articles, topic, target_count)`
2. 当分类或附加 topic 命中以下值时，切换专题 prompt：
   - `游戏+直播`
   - `中国互联网`
3. 未命中特殊 topic 时，继续沿用原来的通用 prompt
4. 后续如果前端扩展频道要升级为后端真实产物，可在生成链路中：
   - 先按 `tags` 汇总候选文章
   - 再调用专题 prompt 进行筛选
   - 输出新的专题 RSS 或专题 JSON

#### 推荐代码落点
- `news_agent/filters/ai_news_filter.py`
  - 增加专题 prompt 模板与路由逻辑
- `scripts/build_cumulative_feed.py`
  - 若后续需要真正生成专题频道，可在这里增加 tag-based category/topic 处理
- `config/rss_feed_urls.json`
  - 已有 `tags` 字段，可直接作为后续 topic 生成依据

### 10. 当前仍可继续优化的点

- 首页当前是“最小可用版”，可继续增强：
  - 增加更多频道/筛选器
  - 显示摘要、来源名、发布时间排序
  - 加入搜索/关键词过滤
- RSS 内部路径目前为：
  - 首页访问使用 `./outputs/feed/*.xml`
  - feed 自身的 `<link>` / `<atom:link>` 已改为 GitHub Pages 域名
- 可继续扩充更多中文商业源，并逐步验证可访问性
- 可把前端聚合频道升级为“按真实 source tags 渲染”
- 可把 AI 筛选从通用分类升级为“按专题 prompt 精准筛选”

## 推荐中文商业/科技补充源（已验证/优先方向）

建议优先保留或继续使用：
- 量子位
- InfoQ 中文网
- 钛媒体
- 少数派
- 机器之心（BestBlogs 转换源）
- 极客公园（BestBlogs 转换源）
- 晚点 LatePost（BestBlogs 转换源）
- 创业邦（BestBlogs 转换源）
- 42章经（BestBlogs 转换源）
- 甲子光年（BestBlogs 转换源）
- 白鲸出海（BestBlogs 转换源）
- 硅星人 Pro（BestBlogs 转换源）
- 吴晓波频道（BestBlogs 转换源）
- 刘润（BestBlogs 转换源）
- 经纬创投（BestBlogs 转换源）
- 暗涌 Waves（BestBlogs 转换源）
- 有新 Newin（BestBlogs 转换源）
- 网易科技（BestBlogs 转换源）
- 腾讯科技（BestBlogs 转换源）
- 深网腾讯新闻（BestBlogs 转换源）

## Workflow 说明

### 自动更新
- 文件：`.github/workflows/daily-update.yml`
- 作用：
  1. 生成累积新闻
  2. 生成 RSS Feed
  3. 提交结果
  4. 部署 GitHub Pages

### 手动重建
- 文件：`.github/workflows/manual-test.yml`
- 当前已升级为适配新结构的 **Manual Rebuild Test**
- 可手动指定：
  - `max_articles`
  - `category`（AI / Technology / Finance）
  - `no_ai_filter`
- 同时会：
  - 重建 RSS
  - 提交结果
  - 重新部署 Pages

### Pages 部署
- 文件：`.github/workflows/pages.yml`
- 作用：将 `index.html` + `outputs/` + `data/` 发布到 GitHub Pages

## 继续接手时建议优先看

1. `config/rss_feed_urls.json`
   - 当前新闻源配置入口（已包含 tags / candidate 状态）
2. `news_agent/filters/ai_news_filter.py`
   - 当前 Gemini 筛选逻辑；后续专题 prompt 优先在这里落地
3. `scripts/build_cumulative_feed.py`
   - RSS 生成逻辑，已修 base_url
4. `scripts/build_cumulative_news.py`
   - 累积新闻生成逻辑
5. `index.html`
   - 当前最小可用前端首页（已加两个扩展频道）
6. `.github/workflows/daily-update.yml`
   - 自动主流程
7. `.github/workflows/manual-test.yml`
   - 手动重建入口
8. `.github/workflows/pages.yml`
   - Pages 发布流程

## 下一步可选方向

### A. 产品化增强
- 首页增加来源名、摘要、排序、搜索、频道数量统计
- 支持更多 feed 在页面中切换展示
- 将扩展频道改为真正按 source tags 聚合，而非仅关键词匹配

### B. 源质量治理
- 给 `config/rss_feed_urls.json` 增加健康检查
- 自动标记超时/失效源
- 坏源不阻塞整体流程

### C. 专题化增强（DOYU / HUYA）
- 为 `游戏+直播` 和 `中国互联网` 增加专用 Gemini 筛选 prompt
- 让扩展频道从“前端聚合”升级到“后端专题筛选 + 专题产物”
- 后续可进一步扩展为：直播、电竞、游戏、平台经济、中概互联网等多个专题

### D. 中文商业源继续扩充
- 持续从 BestBlogs / wechat2rss 中挑选更相关的中文商业、投资、互联网内容源
- 做一轮“可拉取 / 不可拉取”持续验证
