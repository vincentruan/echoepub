# 启用 AI 图片描述功能指南

## 当前状态

✅ **代码增强功能已启用**：
- 代码块自动包装为 ```java
- 代码关键字自动高亮为 `CPool.GetServiceConnection()`

⚠️ **AI 图片描述未启用**（使用占位符模式）

## 启用 AI 图片描述

### 方法1：设置环境变量（推荐）

```bash
# 1. 设置 SiliconFlow API Key
export SILICONFLOW_API_KEY="your_api_key_here"

# 2. 运行处理
cd /Users/vincentruan/vscode_space/echoepub
python .claude/skills/markdown-to-audioread/scripts/audioread_processor.py \
  "books/架构师之路-original_markdown/70_\"id串行化\"到底是怎么实现的？.md"
```

### 方法2：永久设置环境变量

```bash
# 添加到 ~/.zshrc 或 ~/.bash_profile
echo 'export SILICONFLOW_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### 方法3：在命令中直接设置

```bash
SILICONFLOW_API_KEY="your_api_key_here" \
python .claude/skills/markdown-to-audioread/scripts/audioread_processor.py \
  "books/架构师之路-original_markdown/70_\"id串行化\"到底是怎么实现的？.md"
```

## 获取 API Key

1. 访问 [SiliconFlow 官网](https://siliconflow.cn/)
2. 注册账号
3. 在控制台获取 API Key
4. 将 API Key 设置为环境变量

## 效果对比

### 当前（占位符模式）

```markdown
![](./images/00/image_140.jpg)

> **图片说明**：这是一张示意图。
> **核心内容**：展示相关内容
> **关键元素**：请查看原图片获取详细信息
>
> **要点总结**：
> - 第一，该图片为重要示意图，建议查看原图。
> - 第二，图片包含关键信息，有助于理解正文内容。
> - 第三，AI图片描述功能暂未启用或分析失败。
```

### 启用 AI 后（专业模式）

```markdown
![](./images/00/image_140.jpg)

> **图片说明**：这是一个典型的高可用 SOA 架构图。
> **核心内容**：该图展示了一个基于 Nginx 接入、业务逻辑与原子服务解耦、并实现从 Web 层到 DB 层全链路冗余的经典高可用架构。
>
> **要点总结**：
> - 第一，接入层采用 Nginx 反向代理实现负载均衡。
> - 第二，Web 业务层与 Service 服务层分离，体现服务化拆分思想。
> - 第三，除 Cache 层外，所有节点均通过集群化（Cluster）消除单点故障。
```

## 代码增强功能（已启用）

无论是否启用 AI 图片描述，以下功能都会自动执行：

### ✅ 代码块包装

```markdown
修复前：
void work_thread_routine(){
Task t = TaskQueue.pop();
...
}

修复后：
```java
void work_thread_routine(){
Task t = TaskQueue.pop();
...
}
```
```

### ✅ 代码关键字高亮

```markdown
修复前：
CPool.GetServiceConnection()
CPool.GetServiceConnection(long id)
ServiceConnection
MAX_SIZE

修复后：
`CPool.GetServiceConnection()`
`CPool.GetServiceConnection(long id)`
`ServiceConnection`
`MAX_SIZE`
```

## 完整处理流程

```bash
# 1. 设置 API Key
export SILICONFLOW_API_KEY="sk-..."

# 2. 处理单个章节
python .claude/skills/markdown-to-audioread/scripts/audioread_processor.py \
  "books/架构师之路-original_markdown/70_\"id串行化\"到底是怎么实现的？.md"

# 3. 或处理整个文件夹
python .claude/skills/markdown-to-audioread/scripts/audioread_processor.py \
  "books/架构师之路-original_markdown/"
```

## 功能总结

| 功能 | 状态 | 说明 |
|------|------|------|
| 图片描述（AI） | ⚠️ 需启用 | 需要 API Key |
| 图片描述（占位符） | ✅ 已启用 | 默认模式 |
| 二维码跳过 | ✅ 已启用 | 黑名单自动过滤 |
| 代码块包装 | ✅ 已启用 | 自动识别语言 |
| 关键字高亮 | ✅ 已启用 | 函数、类名、常量 |
| 章节导语 | ✅ 已启用 | 自动生成 |
| 章节总结 | ✅ 已启用 | 自动生成 |
| 内容翻译 | ✅ 已启用 | 检测英文段落 |
| 表格转换 | ✅ 已启用 | 转为语音格式 |
| 列表转换 | ✅ 已启用 | 转为语音格式 |
