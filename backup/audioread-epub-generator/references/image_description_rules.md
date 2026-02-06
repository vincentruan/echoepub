# Image Description Rules Reference

## Core Principle

Generate readable, structured descriptions for all images and charts. Descriptions must be suitable for audio narration.

## Required Structure

For every image/chart, include at minimum:

1. **Type identification** (one sentence)
2. **Core conclusion** (1-2 sentences)
3. **Key elements narration** (detail based on type)
4. **Summary points** (3-7 short items)
5. **Uncertainty disclaimer** (if applicable)

## Type-Specific Guidelines

### Charts and Graphs

**What to narrate:**
- X-axis and Y-axis meanings
- Overall trend (increasing, decreasing, fluctuating, stable)
- Peak/valley points and their significance
- Comparison between data series
- Anomalies or notable patterns

**Example format:**
```
![GDP Growth Chart](./images/chart.jpg)

> **图表说明**：这是一张折线图，展示了2020年至2024年GDP增长率的变化趋势。
> 核心结论是：GDP增长率在2020年达到低谷后，于2021年快速反弹，随后呈现稳步下降趋势。
> 关键元素包括：横轴代表年份，纵轴代表GDP增长率百分比；红色曲线代表实际增长率，蓝色曲线代表预测值。
> 要点总结：
> - 第一，2020年受疫情影响，增长率跌至2.3%。
> - 第二，2021年快速反弹至8.1%，创下近年新高。
> - 第三，2022年至2024年逐年回落，回归常态。
> - 第四，预测显示2024年约为5.2%。
> - 第五，实际值与预测值在2023年后出现偏差。
> - 第六，整体趋势符合经济周期规律。
> - 第七，曲线在2021年出现明显拐点。
```

### Flowcharts and Process Diagrams

**What to narrate:**
- Start point (where process begins)
- Sequential steps in order
- Branch conditions and decision points
- End point or output

**Example format:**
```
![User Registration Flow](./images/flowchart.jpg)

> **图表说明**：这是一张用户注册流程图，展示了从访问网站到完成注册的完整流程。
> 核心结论是：整个流程包含三个主要阶段，用户在每个阶段都有退出的选项。
> 关键元素包括：流程从"访问注册页面"开始，依次经过"填写表单"、"验证邮箱"、"设置密码"，最后以"注册成功"结束。
> 要点总结：
> - 第一，流程起点是访问注册页面。
> - 第二，用户需填写基本信息，包括邮箱和用户名。
> - 第三，系统发送验证邮件，用户点击链接完成验证。
> - 第四，用户设置登录密码。
> - 第五，验证成功后显示注册成功页面。
> - 第六，每个步骤下方都有"返回"选项，用户可随时退出。
> - 第七，整体流程线形清晰，采用从上到下的布局。
```

### Architecture and System Diagrams

**What to narrate:**
- Main components and their roles
- Relationships and connections between components
- Data flow direction
- External interfaces or connections

**Example format:**
```
![System Architecture](./images/architecture.jpg)

> **图表说明**：这是一张系统架构图，展示了微服务系统的整体结构。
> 核心结论是：系统采用三层架构，包含网关层、服务层和数据层。
> 关键元素包括：顶部的API网关负责请求路由和认证；中间的服务层包含用户服务、订单服务和支付服务；底部的数据层包含数据库和缓存。
> 要点总结：
> - 第一，所有外部请求首先通过API网关。
> - 第二，网关进行身份验证和流量控制。
> - 第三，用户服务处理账户相关操作。
> - 第四，订单服务处理订单创建和查询。
> - 第五，支付服务处理支付流程。
> - 第六，服务层通过数据库持久化数据。
> - 第七，Redis缓存用于提高读取性能。
> - 第八，服务间采用异步消息队列通信。
```

### Comparison and Before-After Diagrams

**What to narrate:**
- What is being compared (left vs right, before vs after)
- Key differences highlighted
- Outcome or improvement

**Example format:**
```
![Performance Comparison](./images/comparison.jpg)

> **图表说明**：这是一张性能对比图，左侧展示优化前，右侧展示优化后。
> 核心结论是：优化后系统响应时间减少了60%，吞吐量提升了3倍。
> 关键元素包括：左侧柱状图代表优化前的各项指标，右侧柱状图代表优化后的指标，中间用箭头标示改进方向。
> 要点总结：
> - 第一，响应时间从500毫秒降至200毫秒。
> - 第二，每秒请求数从100增加到300。
> - 第三，CPU利用率从80%降至40%。
> - 第四，内存使用保持稳定。
> - 第五，错误率从2%降至0.1%。
> - 第六，所有指标均有明显改善。
> - 第七，绿色柱状图表示达标指标。
```

### Screenshots and UI Images

**What to narrate:**
- What interface/element is shown
- Key fields or buttons
- Current state or configuration
- Important numbers or status indicators

**Example format:**
```
![Dashboard Screenshot](./images/screenshot.jpg)

> **图片说明**：这是系统仪表盘界面的截图。
> 核心结论是：当前系统运行状态良好，关键指标均在正常范围内。
> 关键元素包括：顶部显示系统名称"数据监控平台"；左侧导航栏包含概览、告警、设置等菜单；中间区域显示四个数据卡片和一张实时曲线图。
> 要点总结：
> - 第一，当前用户数为1,234人。
> - 第二，今日新增用户89人。
> - 第三，系统运行时间45天。
> - 第四，告警数量为0，状态良好。
> - 第五，实时曲线显示近一小时访问量。
> - 第六，曲线呈现平稳上升趋势。
> - 第七，界面采用蓝色主题，布局清晰。
```

### Uncertainty Handling

When image is blurry, unclear, or incomplete:

```
> 注：由于图片模糊，部分细节无法确认，以上描述基于可见内容推断，可能存在偏差。
```

## Blacklist: Skip These Image Types

Do NOT add descriptions for:
- **Emoji/stickers**: 纯表情包、网络梗图
- **Portrait photos only**: 纯人物头像、作者照片
- **Pure decorations**: 背景花纹、分隔线、无内容的抽象图案
- **Blurred/unreadable**: 严重模糊或损坏的图片
- **Exact text duplication**: 图片内容与正文逐字重复

## Summary Point Guidelines

- Use 3-7 points per image
- Start with ordinal words: 第一、第二、第三...
- Keep each point under 50 characters
- Focus on insights, not obvious observations
- Group related points together

## Formatting in Markdown

```
![Alt text](image_path)

> **图表说明**：[Type identification]
> 核心结论是：[Core conclusion]
> 关键元素包括：[Key elements narration]
> 要点总结：
> - 第一，[point 1]
> - 第二，[point 2]
> - ...
> - 第N，[point N]
```
