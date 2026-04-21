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

这些源在本轮检测中表现为超时、500、证书异常或域名问题，后续如需可继续复测：
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

### 5. 当前仍可继续优化的点

- 首页当前是“最小可用版”，可继续增强：
  - 增加更多频道/筛选器
  - 显示摘要、来源名、发布时间排序
  - 加入搜索/关键词过滤
- RSS 内部路径目前为：
  - 首页访问使用 `./outputs/feed/*.xml`
  - feed 自身的 `<link>` / `<atom:link>` 已改为 GitHub Pages 域名
- 可继续扩充更多中文商业源，并逐步验证可访问性

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
   - 当前新闻源配置入口
2. `scripts/build_cumulative_feed.py`
   - RSS 生成逻辑，已修 base_url
3. `scripts/build_cumulative_news.py`
   - 累积新闻生成逻辑
4. `index.html`
   - 当前最小可用前端首页
5. `.github/workflows/daily-update.yml`
   - 自动主流程
6. `.github/workflows/manual-test.yml`
   - 手动重建入口
7. `.github/workflows/pages.yml`
   - Pages 发布流程

## 下一步可选方向

### A. 产品化增强
- 首页增加来源名、摘要、排序、搜索、频道数量统计
- 支持更多 feed 在页面中切换展示

### B. 源质量治理
- 给 `config/rss_feed_urls.json` 增加健康检查
- 自动标记超时/失效源
- 坏源不阻塞整体流程

### C. 中文商业源继续扩充
- 持续从 BestBlogs / wechat2rss 中挑选更相关的中文商业、投资、互联网内容源
- 做一轮“可拉取 / 不可拉取”持续验证
