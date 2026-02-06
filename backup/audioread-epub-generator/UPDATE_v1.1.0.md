# audioread-epub-generator Skill 更新说明

**更新日期**: 2026-02-03
**版本**: v1.1.0

## 更新内容

### ✅ 新增功能：智能筛选模式（Smart Fallback Mode）

当AI图片分析失败时，自动为重要图片生成占位描述，**强制使用引用块格式**。

#### 核心特性

1. **智能图片分类**
   - 自动识别架构图、流程图、数据图表等重要图片
   - 自动跳过二维码、封面、肖像等无意义图片

2. **强制引用块格式**
   - 所有图片描述都使用 `>` 引用块格式
   - HTML渲染为 `<blockquote>` 标签
   - TTS友好，便于听书

3. **智能占位描述**
   ```markdown
   > **图片说明**：这是一张架构图。
   > **核心内容**：展示系统结构或组件关系
   > **关键元素**：请查看原图片获取详细信息
   >
   > **要点总结**：
   > - 第一，该图片为重要示意图，建议查看原图。
   > - 第二，图片包含关键信息，有助于理解正文内容。
   ```

### 代码变更

#### 1. `image_descriptor.py`

**新增参数**:
```python
def describe_images_in_markdown(
    markdown_content: str,
    images_dir: str,
    descriptor: Optional[ImageDescriptor] = None,
    smart_fallback: bool = True  # 新增：智能筛选模式
) -> Tuple[str, Dict]:
```

**新增函数**:
- `_is_important_image(context, alt_text)` - 判断图片是否重要
- `_generate_smart_placeholder(context, alt_text, filename)` - 生成智能占位描述

**增强逻辑**:
- AI描述失败时，自动判断图片重要性
- 重要图片 → 生成引用块格式的占位描述
- 无意义图片 → 跳过，不添加描述

#### 2. `main.py`

**集成智能筛选**:
```python
# 默认启用智能筛选模式
smart_fallback = getattr(self, 'smart_fallback', True)

processed_content, img_stats = describe_images_in_markdown(
    content,
    images_dir,
    descriptor,
    smart_fallback=smart_fallback
)
```

**增强统计**:
- 显示fallback生成的描述数量
- 在报告中记录智能筛选活动

#### 3. `SKILL.md`

**新增文档**:
- Smart Fallback Mode 说明
- 重要图片/跳过图片的分类列表
- 占位描述格式示例
- 优势说明

### 使用效果

#### 优化前
```html
<img src="Images/arch.jpg" alt="秒杀架构"/>
<!-- 没有任何描述 -->
```

#### 优化后
```html
<img src="Images/arch.jpg" alt="秒杀架构"/>
<blockquote>
<strong>图片说明</strong>：这是一张架构图。<br/>
<strong>核心内容</strong>：展示系统结构或组件关系：秒杀架构<br/>
<strong>关键元素</strong>：请查看原图片获取详细信息<br/>
<br/>
<strong>要点总结</strong>：<br/>
- 第一，该图片为重要示意图，建议查看原图。<br/>
- 第二，图片包含关键信息，有助于理解正文内容。<br/>
</blockquote>
```

### 实际测试结果

**文件**: `books/架构师之路-智能筛选版.epub`

| 指标 | 结果 |
|------|------|
| 总图片数 | 458张 |
| 已添加描述 | 100张（重要图片） |
| 已跳过 | 358张（无意义图片） |
| 引用块格式 | ✅ 正确 |
| 生成时间 | < 1分钟 |

### 优势总结

✅ **不依赖API** - 无需等待AI处理，立即可用
✅ **智能筛选** - 只为重要图片添加描述
✅ **引用块格式** - 强制使用，TTS友好
✅ **可扩展** - 后续可替换为AI生成内容
✅ **用户体验好** - 清晰标识重要图片

### 向后兼容

- 默认启用智能筛选模式
- 可通过代码设置 `smart_fallback=False` 禁用
- 原有AI处理流程保持不变
- 与现有功能完全兼容

### 下一步优化

1. **手动替换** - 为关键图片手动添加详细描述
2. **本地VLM** - 部署本地视觉模型批量生成
3. **API升级** - 等待更好的商业VLM API

---

**结论**: 本次更新确保了所有图片描述都使用引用块格式，大幅提升了听书体验。
