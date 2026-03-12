---
name: markdown-content-enhancer
description: Add contextual descriptions for images (via vision model), code blocks (agent-generated), and tables (agent-generated) in Markdown files. Preserves ALL original content unchanged. Use after input conversion to enrich content for audio/accessibility consumption.
---

# Markdown Content Enhancer

为 Markdown 文件中的图片、代码块、表格添加上下文描述，使内容更适合语音朗读和无障碍访问。

## 核心原则

**忠于原文，仅添加描述。** 除了在图片、代码块、表格下方添加引用块说明外，不得修改任何原文内容。

## 输入要求

标准 Markdown 目录结构（由 `epub-to-markdown-converter`、`pdf-to-markdown-converter` 或 `markdown-converter` 生成）：

```
$原文件名_markdown/
├── 00_目录.md
├── 01_章节.md
├── 02_章节.md
├── images/
│   └── ...
└── $原文件名_report.md
```

## 输出

```
$原文件名_markdown/
├── _enhanced/              # 输出目录（新增）
│   ├── 01_章节.md       # 已增强
│   ├── 02_章节.md       # 已增强
│   └── *_report.md      # 处理报告
├── 00_目录.md           # 不修改
├── 01_章节.md           # 不修改（源文件）
├── images/              # 不修改
└── $原文件名_report.md  # 不修改
```

> 源文件始终不会被修改，所有处理结果输出到 `_enhanced/` 子文件夹。

---

## 处理规则

### 1. 图片描述生成

为有信息增益的图片添加描述，跳过装饰性图片。

#### 跳过的图片类型（无增益）
- 二维码、表情包、贴纸
- 纯装饰图、分隔线、背景图
- 封面图片、作者照片
- 图标/Logo/徽章
- 文件大小 < 500B 的小图（可能是图标）
- 尺寸 < 50x50px 的小图

> **注意**：EPUB 转换后的图片通常较小，阈值已从 2KB 降至 500B 以避免误跳过有意义的架构图、流程图等。

#### 必须描述的图片类型（有增益）
- 统计图：曲线图、柱状图、饼图、散点图
- 架构图：系统架构、网络拓扑、部署架构
- UML图：类图、时序图、状态图
- 流程图、决策树
- 表格截图、数据截图
- 技术示意图、原理图

#### 处理流程

1. **Agent 提取上下文**：读取图片前后各 10 行内容
2. **调用脚本获取原始描述**：
   ```bash
   python scripts/image_descriptor.py <chapter.md> <images_dir>
   ```
   脚本会在图片下方插入 `<!-- IMAGE_DESCRIPTION: ... -->` 注释
3. **Agent 生成最终描述**：
   - 读取脚本返回的原始描述（在 `<!-- IMAGE_DESCRIPTION: ... -->` 注释中）
   - 结合图片前后 10 行上下文
   - 将 API 描述与上下文语境融合，生成连贯的最终描述
   - 删除 `<!-- IMAGE_DESCRIPTION: ... -->` 注释
   - 添加格式化的引用块

#### 输出格式

```markdown
![架构图](./images/01/arch.jpg)

> 【图片描述】这张架构图展示了一个典型的微服务系统结构，包含用户层（Web端和移动端入口）、API网关层负责统一路由和鉴权、三个核心服务（订单服务、用户服务、支付服务），以及底层的MySQL主从数据库集群和Redis缓存，各服务之间通过消息队列进行异步通信。
>
> 结合上文讨论的微服务架构优势，这张图清晰展示了服务拆分后的系统边界和通信方式，为后续章节的详细讲解提供了整体视图。
```

**关键要求：**
- 第一段：图片内容的客观描述（基于 API 返回）
- 第二段：结合上下文的提炼总结（Agent 生成）
- 两段之间空一行
- 使用 `> 【图片描述】` 开头

---

### 2. 代码块描述生成

为有意义的代码块添加功能说明。**由 Agent 直接分析生成，无需调用 API。**

#### 代码块识别规则

**包裹代码块（标准格式）：**
- 以 ``` 开头和结尾的代码块

**未包裹代码块（EPUB 转换常见）：**
- 包含函数定义关键词：`void`、`function`、`def`、`public`、`private`、`class`
- 包含 SQL 语句：`SELECT`、`UPDATE`、`INSERT`、`CREATE`、`DELETE`
- 包含编程语言特征：`return`、`if(`、`for(`、`while(`、`import`、`#include`
- 包含伪代码特征：驼峰命名函数调用（如 `GetConnection()`）、带注释的逻辑流程
- 连续多行包含赋值/调用/控制流语句

**识别方法：** Agent 扫描段落，如果连续 3 行以上包含上述特征，且不在 ``` 包裹中，则识别为未包裹代码块。

#### 跳过的代码块
- 少于 3 行的简单代码
- 单行 import 语句
- 配置片段（JSON、YAML、环境变量）
- 示例输出、日志片段

#### 必须描述的代码块
- 函数/方法实现
- 类定义
- 算法实现
- 关键业务逻辑
- 复杂的数据处理流程
- SQL 查询语句（UPDATE/SELECT 等）
- 伪代码逻辑流程

#### 处理流程

1. Agent 读取代码块内容（包裹或未包裹）
2. Agent 分析代码的功能和关键实现逻辑
3. Agent 生成简洁的功能总结
4. 在代码块后添加引用块（保持原代码不变）

#### 输出格式

````markdown
```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```

> 【代码说明】这段Python代码实现了快速排序算法。其核心逻辑是选取数组中间位置的元素作为基准值，将数组分为小于、等于、大于基准值的三部分，然后对左右两部分递归排序并合并结果，是一种经典的分治算法实现。
````

**关键要求：**
- 说明代码的功能目的（这段代码做了什么）
- 说明关键实现逻辑（怎么实现的）
- 使用 `> 【代码说明】` 开头
- 保持简洁，一般 1-2 句话

---

### 3. 表格描述生成

为有意义的表格添加自然语言描述。**由 Agent 直接分析生成，无需调用 API。**

#### 跳过的表格
- 少于 2 行数据的简单表格
- 纯装饰性表格（如分隔线）

#### 必须描述的表格
- 数据对比表
- 配置参数表
- 性能指标表
- 特性对比表
- 统计数据表

#### 处理流程

1. Agent 读取表格内容
2. Agent 分析表格的主题和数据
3. Agent 生成自然语言描述
4. Agent 结合上下文生成提炼总结
5. 在表格后添加引用块

#### 输出格式

```markdown
| 指标 | 2023年 | 2024年 | 增长率 |
|------|--------|--------|--------|
| GDP | 10.2万亿 | 11.5万亿 | 12.7% |
| 人口 | 14.1亿 | 14.2亿 | 0.7% |

> 【表格说明】这个表格展示了2023年和2024年两年的GDP和人口数据对比。GDP从10.2万亿增长到11.5万亿，增长率为12.7%；人口从14.1亿增长到14.2亿，增长率为0.7%。
>
> 结合上文关于经济发展的讨论，这组数据印证了GDP增速远高于人口增速的趋势，说明人均GDP有显著提升。
```

**关键要求：**
- 第一段：表格内容的文字描述（客观陈述数据）
- 第二段：结合上下文的提炼总结
- 两段之间空一行
- 使用 `> 【表格说明】` 开头

---

## 严格约束

**除上述三类引用块外，不得修改任何原文内容：**
- 不修改段落文字
- 不修改标题
- 不修改列表
- 不修改已有的引用块
- 不修改链接
- 不修改任何 markdown 格式
- 不添加章节导语、总结、或任何非原文内容

---

## Agent 处理流程

当 Agent 使用此技能处理章节时，按以下顺序操作：

1. **读取章节 Markdown 文件**
2. **处理图片**：
   - 调用 `python scripts/image_descriptor.py <chapter.md> <images_dir>`
   - 读取脚本输出，找到所有 `<!-- IMAGE_DESCRIPTION: ... -->` 注释
   - 对每个注释：
     - 提取 API 返回的原始描述
     - 读取图片前后 10 行上下文
     - 将描述与上下文融合，生成最终描述
     - 删除注释，添加格式化的引用块
3. **处理代码块**（包裹和未包裹）：
   - 识别所有 ``` 包裹的代码块
   - 识别未包裹的代码段落（函数定义、SQL语句、伪代码等，连续 3+ 行代码特征）
   - 跳过简单代码（< 3 行、import、配置）
   - 对每个代码块：
     - 分析代码功能和实现逻辑
     - 在代码块后添加 `> 【代码说明】...` 引用块
4. **处理表格**：
   - 识别所有表格
   - 跳过简单表格（< 2 行数据）
   - 对每个表格：
     - 分析表格内容和主题
     - 结合上下文生成提炼总结
     - 在表格后添加 `> 【表格说明】...` 引用块
5. **写入 `_enhanced/` 子文件夹**（源文件不变）
6. **修正图片路径**：将所有图片引用从 `./images/` 改为 `../images/`，因为输出文件在子目录中

---

## 使用方法

```bash
# Agent 调用此技能处理整个文件夹
# 技能会自动：
# 1. 创建 _enhanced/ 输出目录
# 2. 对每个章节文件调用 image_descriptor.py
# 3. Agent 处理图片描述、代码块、表格
# 4. 输出到 _enhanced/ 目录
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ECHO_EPUB_OPEN_API_KEY` | API Key（必须） | - |
| `ECHO_EPUB_OPEN_AI_BASE_URL` | OpenAI 兼容 API 地址 | `https://api.siliconflow.cn/v1` |
| `ECHO_EPUB_VLM_MODEL` | 视觉模型（图片描述） | `Pro/Qwen/Qwen2.5-VL-7B-Instruct` |

> 支持任何 OpenAI 兼容的 API 接口，通过 `ECHO_EPUB_OPEN_AI_BASE_URL` 切换。

---

## 依赖

```bash
pip install requests Pillow
```

---

## 脚本位置

- `scripts/openai_client.py` — API 客户端（图片分析）
- `scripts/image_descriptor.py` — 图片描述生成器
