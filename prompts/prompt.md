调用视觉阅读 @books/Executable Code Actions Elicit Better LLM Agents2402.01030v4.pdf , 并对比 @books/Executable Code Actions Elicit Better LLM Agents2402.01030v4_audio.epub，我发现生成的epub依然没有彻底修复：
  1、正文没有正常翻译，依然是英文的内容
  2、image内容为空，没有合理的展示图片
  3、代码、注释、引用等信息没有用markdown的代码块、引用块等处理，导致展示错乱
  4、其他可能的问题
  上述是我再上一轮优化后，依然发现的问题，可能还存在其他问题，请检查后，继续优化skill `audioread-epub-generator`，优化后，重新生成epub，并调用调用视觉阅读 @books/Executable Code Actions Elicit Better LLM Agents2402.01030v4.pdf , 并对比 @books/Executable Code Actions Elicit Better LLM Agents2402.01030v4_audio.epub，不断循环，直至符合正文翻译为epub的要求





优化skill `audioread-epub-generator`

1、翻译部分的内容，原方案为通过在当前技能上下文直接进行翻译，但实际上可能会造成当前skill内容过于突出，所以，我们需要修改它改为调用api的方式，让他去调用另外一个大模型，实现翻译的能力。

大模型的api调用文档地址为：https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions

其中，model使用MiniMaxAI/MiniMax-M2，也可以通过环境变量`ECHO_EPUB_TRANSLATE_MODEL`指定，

2、图片解析部分，原方案为通过当前技能上下文进行分析，但实际上生成的内容都是`“（引用开始：图片说明：这是一张图片。 引用结束)`这里内容，没有转换成图片的解析，需要修改为：先调用大模型vlm获取图片内容，然后将图片内容结合上下文信息，转换成文本描述，方便用户能够通过听书的方式，清晰的知道图片内容是什么，作者的表达结构是什么？

调用的api地址为：https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions#vlm

其中，model使用PaddlePaddle/PaddleOCR-VL-1.5，也可以通过环境变量`ECHO_EPUB_VLM_MODEL`指定，

调用点的API key默认从环境变量`ECHO_EPUB_OPEN_API_KEY`指定（也可以在提示词中填入）



添加 `ECHO_EPUB_OPEN_AI_BASE_URL`  用于指定openai模型的baseurl，如果没有指定则默认为https://api.siliconflow.cn/v1



阅读 books/架构师之路（58沈剑） (it-ebooks) (Z-Library)_audio.epub  以及原文件 books/架构师之路（58沈剑） (it-ebooks) (Z-Library).epub，
  1、图片没有被正确提取
  2、图片没有被正确的识别和转换成文字描述
  3、删除空白的页面
  原epub的英文都是技术术语，不需要翻译，因此，请使用skill `audioread-epub-generator`修正上述两个问题，修正后再阅读两个epub文件，检查是否出现预期之外的错误，如果是skill的问题，则修正skill，直至生成的epub文件符合预期



```
/ralph-loop:ralph-loop """books/架构师之路（58沈剑）_audio_v3_with_images.epub 是我们基于原文件 books/架构师之路（58沈剑） (it-ebooks) (Z-Library).epub ，通过调用优化skill `audioread-epub-generator`进行生成，但是，我们发现生成的epub在图片下方增加文字描述并没有通过`引用块`框起来，以让epub获取更好的听书体验的目标，请先检查是否出现预期之外的问题（比如生成的文件与源文件样式不对、文字混乱、排版错位等，如果是skill的问题，则修正skill，然后调用skill重新生成新文件，这里需要注意，对于无意义的图片不需要增加说明，比如，图片只是一张二维码、或者一个用于封面的背景图片、或者只是人物肖像等，我们需要增加描述的图片应该符合流程图、架构图、UML、数据表格、饼图、柱状图等包含上下文语义图表，如果skill不满足，则不断优化skill对于epub文件转换的场景""" --completion-promise """检查两份epub直至生成的epub文件与源文件相比，应该只有在符合条件的图片下方增加了文字描述，且内容和排班没有发生错乱""" --max-iterations 20

/ralph-loop:ralph-loop """调用优化skill `audioread-epub-generator`转换原文件 `架构师之路（58沈剑）.epub`，不要修改原文件内容""" --completion-promise """检查生成的epub文件与源文件，我们的核心目标是让最终生成的epub增加图片描述，且图片描述必须使用引用块框起来，来获取更好的听书体验的目标。需要检查是否出现预期之外的问题，比如生成的文件与源文件样式不对、文字混乱、排版错位等，如果是skill的问题，则修正skill，然后调用skill重新生成新文件，这里需要注意，对于无意义的图片不需要增加说明，比如，图片只是一张二维码、或者一个用于封面的背景图片、或者只是人物肖像等，我们只需要增加描述的图片，应该符合流程图、架构图、UML、数据表格、饼图、柱状图等包含上下文语义图表，并且描述内容必须`引用块`（类似markdown`> 引用块内文字`的效果)包裹，如果skill不满足，则不断优化skill""" --max-iterations 20
```



更新skill `audioread-epub-generator`的翻译部分，我们最终希望达到的效果是，该skill能够生成原文的markdown文件、以及翻译后的markdown文件，并且最终的epub只需要翻译后的。

你应该先搜索翻译文档的最佳实践，在翻译里面，我们希望大模型逐段落翻译为中文，并且保留一些专业术语、定义描述。

请先搜索，思考，后更新skill



```markdown
你是一个资深的claude code skills开发专家，阅读当前项目的.claude/skills目录下的所有skills，`audioread-epub-generator`对应的skill存在职能太过集中，反而导致效果不好，我们需要对项目下的所有skill进行优化，请先深入思考，然后结合如下要求进行优化：
## 整体思路
我们的整体思路是将skill拆分成如下多个skill的调用时序，通过claude.md的内容去引导流程编排。
时序为：
`1）读取输入的文件（epub、pdf、markdown)转换成原始markdown（包括图片、附件分离，如果原输入就是markdown，则不需要这个步骤）`->`2）执行转换策略，将markdown转换成收听友好的markdown`->`3）markdown转换成epub`
以上的每个步骤我们都需要在当前项目.claude/skills下结合技能`skill-writer`打磨skill（第一个步骤根据输入的不同可能有多个skill），并在源文件的同级目录下创建一个`$原文件名_report.md`的记录各步骤处理情况报告，用于异常时定位。
## 重构skill `audioread-epub-generator`
`audioread-epub-generator`一次性支持了多种格式的输入，比如epub、pdf、markdown（含文件夹内多个文件），应该拆分成不同读取的skill，后续对于哪个输入的文件应该调用哪个skill处理，应该通过claude.md的内容去引导
1. 将epub（实际调用的`epub` skill）的处理，整合到`epub`技能中，并将`epub`技能升级为`epub-to-markdown-converter`
2. 将pdf的处理（实际调用的是pdf-to-markdown-converter）拆出来，直接使用pdf-to-markdown-converter
3. 将对输入文件的处理策略拆分成独立skill `markdown-to-audioread`（对应时序步骤2）
4. 原skill`audioread-epub-generator`移动到项目的backup文件夹作废
## 优化下述所有skill
将上述拆分后，对应我们的时序，得到的skill应该如下（标记为`当前无需调整`的skill我们会再接下来单独优化）：
### 1）输入的文件（epub、pdf、markdown)转markdown
基于当前需要支持的三个文件类型输入，需要3个skill：
1. `epub-to-markdown-converter`：将现有的`epub`技能进行升级，实现读取epub的内容，按照章节转换成多个markdown文件，markdown的文件列表为一个目录文件、N个章节内容文件（一个章节对应一个markdown文件）
2. `pdf-to-markdown-converter`：调整输出的markdown符合标准格式
3. `markdown-converter`：将输入的markdown文件（也可能是一个文件夹），调用脚本拆分成一个目录文件、N个章节内容文件（一个章节对应一个markdown文件）的文件形式
更多的，我们可以看到，未来对于输入的类型可能是多个，不管是什么样的输入，我们都希望输出是稳定的markdown标准格式，即：产出物为多个markdown，markdown的文件列表为一个目录文件、N个章节内容文件（一个章节对应一个markdown文件），生成的markdown文件列表放在与源文件同名、同级目录的文件夹下，我们需要构建一个用于创建未来扩展输入处理的skill，通过该skill未来能够创建类似`pdf-to-markdown-converter`的skill
### 2）执行markdown转换策略，将markdown转换成收听友好的markdown
 skill `markdown-to-audioread`：将对输入原始文件转换后的markdown文件夹，对N个章节内容文件执行样式、内容检查、文本翻译、图片描述等原`audioread-epub-generator`对输入文件的处理策略
### 3）markdown转换成epub
原逻辑是通过`ebook-processor`调用`markdown-to-epub`进行电子书处理，请更改：
1. 仅保留`markdown-to-epub`，将原`ebook-processor`技能与`markdown-to-epub`进行合并，最终实现将markdown的文件从封面到目录到每个章节的epub电子书生成
2. 合并完成后，将原`ebook-processor`移动到项目的backup文件夹作废
```

