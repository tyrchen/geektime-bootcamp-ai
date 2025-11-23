# Instructions

## code review command

帮我参照 @.claude/commands/speckit.specify.md 的结构，think ultra hard，构建一个对 Python 和 Typescript 代码进行深度代码审查的命令，放在 @.claude/commands/ 下。主要考虑几个方面：

- 架构和设计：是否考虑 python 和 typescript 的架构和设计最佳实践？是否有清晰的接口设计？是否考虑一定程度的可扩展性
- KISS 原则
- 代码质量：DRY, YAGNI, SOLID, etc. 函数原则上不超过 150 行，参数原则上不超过 7 个。
- 使用 builder 模式

## review 代码

@agent-py-arch 帮我仔细查看 ./w2/db_query/backend
的架构，目前因为添加了新的数据库，需要重新考虑整体的设计，最好设计一套 interface，为以后添加更多数据库留有余地，不至于到处修改已有代码。设计要符合 Open-Close 和 SOLID 原则。

## Raflow spec format

将 @specs/w3/raflow/0001-spec.md 的内容组织成格式正确的 markdown 文件，不要丢失任何内容

## 构建详细的设计文档

根据 @specs/w3/raflow/0001-spec.md 的内容，进行系统的 web search 确保信息的准确性，尤其是使用最新版本的 dependencies。根据你了解的知识，构建一个详细的设计文档，放在 ./specs/w3/raflow/0002-design.md 文件中，输出为中文，使用 mermaid 绘制架构，设计，组件，流程等图表并详细说明。

## 实现

根据 @specs/w3/raflow/0002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，完整实现 phase 1。
