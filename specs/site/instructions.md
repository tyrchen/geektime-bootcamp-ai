# Instructions

## 构建 MDX presentation site

帮我在 ./presentations 目录下构建一个 MDX app。使其可以展示 mdx 文件。然后，根据你对 NotebookLM 的理解，为这个应用添加一个 NotebookLM 的深度介绍，并辅以 mermaid diagram 来介绍其架构，flow等。

## 介绍 claude / openai / google gemini 的差异

Think ultra-hard，帮我构建一个 claude / openai / google gemini 的差异对比的 mdx 文件，并辅以 mermaid diagram 来介绍其架构，flow等。

## 介绍 claude code / cursor / codex 的差异

Think ultra-hard，帮我构建一个 claude code / cursor / codex 的差异对比的 mdx 文件，并辅以 mermaid diagram，每个 diagram 有详细信息说明，来介绍其架构，flow等。

## 构建为了演示效果的 components

读取目前已有的 mdx 文件，思考如何构建更具有视觉冲击力，交互性的 components，提升演示效果，比如对比展示 claude / openai / google gemini 差异时，漂亮的表格，或者 card 展示，会添色不少。

## 构建 presentation 的 CLAUDE.md

在 ./presentations 目录下生成一个简单的 CLAUDE.md，要求每次生成新的 mdx 文件时，首先思考需要哪些组件来生动地呈现内容，然后对给定主题进行网络搜索以确保知识是最新的。完成后，使用 playwright 运行页面，截取快照，确保一切看起来正确（对于交互部分，执行操作后也要截取快照）。

## 安装 claude code

think ultra hard, 生成安装 claude code，使用 subscription 账号，以及使用 aws bedrock 的方法，对比二者优缺点，生成 mdx 文件。

## 阅读 claude code 的文档

仔细研读 claude code 代码 /Users/tchen/.local/state/fnm_multishells/90987_1762672421064/bin/claude，找出其各种 system prompt，存在 presentations/prompts 下，并分析其代码和 system prompt，写一篇非常详尽的介绍 claude code 架构和设计的文档，使用 mermaid 绘制架构，设计，组件，流程等图表并详细说明。

## 构建 website

使用 astro framework 构建 "陈天的极客时间 AI 训练营" 课程 website，构建必要的 component，色调和样式参考苹果网站的设计风格，简约高雅，动画效果干净具有美感。课程大纲如下，请根据它设计 website 的信息架构，并构建相应的页面，每个涉及到的工具都有其相应的页面，并辅以 mermaid diagram 来介绍其架构，flow等。比如 cursor, claude code, notebooklm 等。每周的课程都会有若干小节，每个小节有其相应的页面。页面要具有良好的展示性和交互性，避免过多的文字（可以 expand 看详细内容），多使用图片，图表，动画来展示内容。think ultra hard，build a design/implementation plan at ./specs/0003-ai-training-camp.md，使用中文。

```txt
课程核心价值
本课程旨在赋能研发团队，掌握将 AI 大模型和前沿智能工具（如 OpenAI、Gemini、Claude、Cursor 等）无缝融入软件开发全生命周期的核心技能。通过系统化的理论学习与高度实践导向的演练，学员将能够：
实现代码智能辅助与自动化：借助 AI 工具实现代码生成、重构、错误排查等，大幅提升编码效率与质量。
深度理解与快速掌握代码库：利用 AI 快速分析和理解大型、复杂的代码库，加速新人上手和跨项目协作。
自动化文档与设计：高效生成项目文档、设计方案、架构图及流程图，将繁琐的文档工作自动化。
构建与利用智能体：学习搭建和定制 AI Agent，实现智能体间的协作，以应对更复杂的开发任务。
最终，本课程将帮助个人和团队显著提升研发效能、优化开发流程，并激发持续的创新能力。

学完课程后的收益
精通 AI 编码与辅助工具：熟练掌握并灵活运用 Claude Code、Cursor、NotebookLM 等尖端 AI 工具，将日常开发效率推向新高。
深化大模型应用洞察：深入理解 Gemini、OpenAI、Claude 等主流大模型在编码、系统分析、架构设计等各环节的巨大潜能。
贯穿全流程的 AI 赋能实践：掌握从需求洞察、竞品分析到任务拆分和编码实现的全链路 AI应用方法，尤其专注于如何高效掌握新代码库和生成高质量技术文档。
构建专业级 AI 基础设施：学习并实践 MCP 协议，为团队构建私有 MCP 服务器，为智能体提供精准、实时的上下文支持。
定制化智能体核心：掌握构建通用智能体核心的方法，能够根据具体业务需求快速开发和部署面向特定任务的 AI Agent。
全面提升团队研发效能：通过 AI 工具和新工作流的引入，显著优化开发流程，提升团队协作效率与最终产品质量。

用户的入学基础要求
本课程面向所有希望通过 AI 提升工作效率的开发者，并有以下基础要求：
编程基础：至少熟悉一种主流编程语言（如 TypeScript/Python/Rust/Golang 等）的基本语法，生态系统和常用框架。无需精通特定语言，课程内容与代码均将由 Cursor 或  Claude Code 辅助完成，所有的调试和纠错过程也基于对产品需求的理解而非对语言本身的理解。
开发流程认知：对软件开发的基本生命周期（需求、设计、编码、测试、部署）有基本概念。
版本控制技能：熟悉 Git 等主流版本控制工具的使用。
学习热情：对 AI 技术有基本认知，并对探索大语言模型（LLM）在开发领域的应用充满热情。

课程大纲
第一周：AI 编码新范式：工具启蒙与快速实践
学习目标
认知工具全貌：建立对 AI 辅助工具生态的初步认知，了解 NotebookLM、Cursor、Claude Code 等工具在软件开发中的定位与应用场景。
掌握核心基础：了解主流大语言模型（如 Gemini、OpenAI、Claude）的核心能力，掌握  API 接入与基本使用方法。
零基础快速上手：完成 Cursor 与 Claude Code 的安装配置，并熟练掌握其基础操作，为后续深度学习打下坚实基础。
完成首个 AI 项目：借助 AI 辅助，快速构建一个简单的项目管理工具原型，亲身体验 AI 赋能的编码效率。
知识点
AI 辅助工具生态概览：涵盖 AI 原生代码编辑器（Cursor、Claude Code）和知识管理工具（NotebookLM）。
主流大语言模型（LLM）初探：介绍模型核心能力与 API 接入配置。
AI 工具环境搭建与核心功能：涵盖 Cursor/Claude Code 环境配置、基础功能（聊天、命令面板等）初探。
项目原型实践：介绍项目需求提炼与基础代码片段生成。

第二周：深入 Cursor：人机交互式智能编程
学习目标
精通 Cursor 高级功能：掌握其独特的Rules设置、文档集成与多模态交互技巧。
实践“规划-设计-实现-回顾”流程：以 Cursor 为核心工具，将 AI 深度融入软件开发全流程，重点练习代码补全、解释、重构与测试辅助。
实战项目：构建一个数据库查询工具，实现通过 AI 生成 SQL 查询的核心功能。
知识点
Cursor核心功能：文档与项目上下文（@文档集成）、行为定制化（Rules设置）、交互式编程（智能补全、聊天模式）。
AI 辅助流程实践（以 Cursor 为例）：需求分析与原型、代码实现与调试、质量保障（测试用例生成）。
实践：基于“规划-设计-实现-回顾”流程，使用 Cursor 设计并实现一个能连接数据库、并通过自然语言输入由 AI 生成和执行 SQL 查询的工具。

第三周：深入 Claude Code：Agent 驱动的自动化开发
学习目标
精通 Claude Code 高级功能：掌握其独特的Command、Agent与Hook等自动化功能。
理解 AI Agent 工作原理：学习如何通过定制化 Agent 实现复杂、多步骤的自动化任务。
实践：为第二周构建的数据库查询工具添加更多数据库支持。
知识点
Claude Code 核心功能：任务自动化（Command）、Agent 核心（构建自定义 Agent）、文档集成（@）。
AI Agent 工作流实践：任务分解、Agent 协作模式、Agent 在代码审查、API 文档生成等自动化任务中的应用。

第四周：高效解构：AI 赋能下的代码库深度理解与文档化
学习目标
掌握 AI 代码研究方法：学习并应用 AI 工具（Cursor、Claude Code）快速、系统地解构并深度理解大型开源项目（如 OpenAI Codex 和 Microsoft Autogen）的核心代码库。
将洞察转化为专业文档：熟练运用 AI 辅助，将对代码的理解系统性地转化为高质量的技术方案设计和架构设计文档。
掌握 AI 驱动的可视化表达：利用 AI 工具自动或半自动生成流程图、时序图、架构图等，实现复杂逻辑的清晰可视化。
建立高效工作流：整合 AI 工具，建立一套从代码研究、文档撰写到可视化呈现的完整、高效的工作流。
知识点
核心代码库研究方法论：AI 辅助的代码理解策略（自顶向下、自底向上、关键路径分析）、多源上下文管理。
AI 辅助技术文档撰写：方案设计自动化、架构设计智能辅助。
AI 驱动的可视化生成：AI 将代码或自然语言描述转化为 Mermaid、Excalidraw 等格式的图表。
实践：以 Codex/Autogen 的核心模块为例，使用 Cursor 和 Claude Code 理解其工作原理，并输出一份详细的中文设计分析和流程图。

第五周：深入学习和使用 MCP
学习目标
精通协议原理：深度理解 MCP (Model Context Protocol) 协议的核心概念、工作机制与设计哲学。
掌握架构角色：明确 MCP Client（如 Cursor）与 MCP Server 的角色分工与高效交互模式。
亲手打造核心工具：学习并实践如何从零开始构建一个功能全面、可调用的 MCP Server。
实现 AI 知识增强：将自建的 MCP Server 无缝集成至 AI 工具，为智能体提供精准、实时的外部知识。
知识点
攻克 LLM 的致命痛点：深入剖析 LLM 上下文窗口限制与知识滞后性带来的挑战。
MCP 协议详解：核心机制、协议设计思想。
MCP Server 架构与实现：数据源集成、向量化检索（RAG）、API 接口设计。
MCP Client 调用实践：深入理解 Cursor 等工具如何通过 MCP 协议，智能地向外部知识源请求信息并应用。
实践：构建一个包含 shell 访问，文件处理，以及 Postgres 数据库访问的 MCP Server。

第六周：Agent 核心：从逆向工程到通用智能体构建
学习目标
理解 AI Agent：深入理解智能代理 (AI Agent) 的概念及其在复杂开发任务中的应用。
逆向工程与架构洞察：通过分析 Claude Code 和 OpenAI Codex，洞察复杂 AI Agent 的底层工作原理和设计思路。
构建通用 Agent 核心：亲手编写一个支持复杂多轮对话的 Agent 内核，为未来构建特定智能体奠定基础。
实践定制化应用：基于自建的 Agent 核心，开发一个强大的 Code Review Agent，并用于实际代码审查。
知识点
AI Agent 核心原理与设计模式。
多 Agent 协作与任务流编排。
Claude Code 与 Codex 的 Agent 架构分析。
通用 Agent 内核的实现要点。
实践：构建一个通用 Agent 内核，并在此基础上实现一个功能强大的 Code Review Agent。

第七周：AI 赋能软件开发全流程端到端实践
学习目标
综合运用 AI 工具：掌握如何整合 NotebookLM, 大模型的高级检索功能, Cursor、Claude Code 等，贯通软件开发全流程。
构建端到端工作流：学习并实践从需求分析、竞品研究到任务分解、编码实现、文档编写的完整 AI 辅助开发流程。
深化工具间协同：掌握在不同开发阶段选择和切换 AI 工具的策略。
知识点
早期阶段 AI 应用：NotebookLM 在需求与技术预研中的应用。
设计与规划阶段：大模型的高级检索与分析能力在设计方案生成中的应用。
编码与任务管理：利用 Cursor 的 Memory Bank 或 Claude Code 的自定义命令进行有效的任务分解与上下文管理。
全流程实践案例：以小型完整功能模块为例，演练从需求理解到最终代码提交的完整流程。
实践：选择一个小型功能模块，按照本周学习的全流程方法，使用一系列 AI 工具完成其开发，并与课程第一周的原型项目进行对比。

第八周：回顾与展望：AI 在软件工程的未来
学习目标
知识体系梳理： 全面回顾并巩固课程中介绍的所有核心概念、AI 工具和方法论。
洞察未来趋势： 探讨 AI 编码领域的未来发展方向，以及个人和团队如何保持持续学习。
知识点
核心 AI 工具与技术串讲： Prompt Engineering、MCP、RAG、AI Agents 等。
AI 赋能软件开发流程最佳实践： 各环节的优化策略与案例分析。
未来展望： 编程范式、编程语言、验证机制、软件开发的终极方式等。

课程的实战项目
实战一：AI驱动的“从零到一”：项目管理工具的开发
总体目标：快速掌握 AI 工具的核心功能，并将其应用于实用的原型构建，体验 AI 辅助编码的效率。

核心要点：
使用 Cursor AI 辅助生成前端/后端基础代码，实现任务创建、查看、状态变更等基本功能。

实战二：双剑合璧：智能数据库查询与全流程实践
总体目标： 深入掌握 Cursor 和 Claude Code 在全流程开发中的应用，构建一个中等规模的智能数据库工具。

核心要点：
基于 “规划-设计-实现-回顾” 流程，使用 Cursor 设计并实现一个能连接数据库、并通过自然语言输入由 AI 生成和执行 SQL 查询的工具。
重点练习 Cursor 的代码生成、调试辅助及测试用例生成。

实战三：大型代码库理解/MCP 服务器
总体目标：利用 AI 工具提升对复杂代码库的理解效率，并构建私有 MCP 服务器。

核心要点：
新代码库理解与文档生成：以 codex/autogen (或其他指定开源项目) 为例，使用 Cursor 和 Claude Code 深入分析其核心模块，输出模块设计文档和关键流程图。
私有 MCP Server 构建：构建一个包含 shell 访问，文件处理，以及 Postgres 数据库访问 MCP server。

实战四：Agent 核心与智能体定制：构建你的专属 Agent
总体目标：探索并实践 AI Agent 在软件开发自动化中的核心应用，掌握从零构建定制化 Agent 的能力。

核心要点：
掌握通用 Agent 内核的设计原理。
设计并实现一个能够对特定语言代码进行风格检查、逻辑建议和潜在漏洞分析的 Code Review Agent。

实战五：端到端 AI 赋能的软件开发全流程实践
总体目标：将课程所学的所有 AI 工具与方法论融会贯通，完整实践一个从需求到交付的全链路 AI 辅助项目。

核心要点：
运用 NotebookLM 进行需求分析和技术预研。
利用大模型 Deep Research 能力生成设计方案。
通过 Claude Code 进行任务分解。
在 Cursor / Claude Code 中全程 AI 辅助完成编码、测试和文档编写。
```

## search web

make sure you search the web carefully to make sure you get latest info, e.g. claude code is 2.0 now, cursor is 2.0. Sonnet 4.5 has 1m
token context, etc. Always do web search to make sure your knowledge up to date.

## port mdx docs into site

Now add a section "学习资料" after "实战项目", and help me port mdx docs in ./presentations into the ./site and link them in the right places (e.g. project, tools, etc.) properly. Make sure the themes and colors (esp. mermaid chart) are aligned with the sites. Port the components over when necessary and make sure the theme, style and colors are correct. Think hard and make a good plan, then implement it.

## 构建 cursor 的完整的学习资料

深度思考，查阅网上资料，帮我撰写一个 ./site/src/pages/materials/cursor-intro.mdx 文件，内容为 cursor 的完整的学习资料，包括 cursor 的架构，设计，组件，流程等，使用 mermaid 绘制架构，设计，组件，流程等图表并详细说明。然后再介绍 cursor 的 rules 和 agent 的用法。

## 构建 claude code 的完整的学习资料

深度思考，查阅网上资料，帮我撰写一个 ./site/src/pages/materials/claude-code-intro.mdx 文件，内容为 claude code 的完整的学习资料，包括 claude code 的架构，设计，组件，流程等，使用 mermaid 绘制架构，设计，组件，流程等图表并详细说明。然后再介绍 claude code 的 hooks, command 和 agent 的用法。

## 详细介绍如何添加 cursor rules

深度思考，查阅网上资料，帮我撰写一个 ./site/src/pages/materials/cursor-rules-guide.mdx 文件，内容为如何添加 cursor rules，包括 cursor rules 的结构，设计，组件，流程等，使用 mermaid 绘制架构，设计，组件，流程等图表并详细说明。然后再介绍 cursor rules 的用法。

## 更新项目 1

深度学习 ./site，根据 ./w1/project-alpha 的 specs 深度了解项目 1，并更新 ./site 里跟项目 1 相关的内容。项目的截图使用 playwright 生成，并保存到 ./site/public/images/projects/project-1/ 目录下。

## 生成图片

仔细阅读 ./site 代码，看哪些地方缺图片（或者使用图片效果更好），使用 ai image skill 生成图片，保存到 ./site/public/images/ 目录下，并在需要图片的页面中引用。如果不是需要特别风格的图片，尽量生成 ghibli 风格的图片。

## 详细介绍 speckit

深度思考，查阅网上资料，帮我撰写一个 ./site/src/pages/materials/speckit-intro.mdx 文件，内容为 speckit 的完整的学习资料，包括 speckit 的架构，设计，组件，流程等，使用 mermaid 绘制架构，设计，组件，流程等图表并详细说明。然后再介绍 speckit 的用法。

## 更新 claude code arch doc

based on @w3/extracted/system-prompts.json and @w3/extracted/tool-definitions.json update
@site/src/pages/materials/claude-code-architecture.mdx. Also make sure the page follow the design token for
./site

## claude code hooks 文档

查阅官方文档和网上资料，帮我各撰写一篇 claude code hooks/skills 的深度分析和使用介绍的 mdx 文档，注意使用 ./site 的 design token，放在 @site/src/pages/materials/ 下。

## 添加文档

帮我生成一篇详细的技术文档，放在： ./site/src/pages/materials/transcribe-internals.md。根据 raflow项目所学的知识，同时搜索网络进行 deep research，详细介绍：1. 为什么需要重采样 48khz 立体声 -> 16khz 单声道，AI 模型为什么在 16khz PCM 上训练？2. 如何进行 echo cancellation，如何进行静音检测，为何这些没做好 elevenlabs realtime API 效果表现不佳？3.
无锁设计在这样的 app 里为什么很重要？
