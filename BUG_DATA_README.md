# Bug 数据提取工具使用说明

这个工具用于提取和分析 Defects4C 仓库中的所有 bug 数据。

## 快速开始

### 运行提取脚本

```bash
python3 extract_bug_data.py
```

这将在 `bug_data_output/` 目录下生成以下文件：

- `all_bugs.json` - 所有 bug 的完整 JSON 数据
- `all_bugs.csv` - CSV 格式，可用 Excel 打开
- `statistics.json` - 详细统计数据
- `PROJECT_SUMMARY.md` - 项目和 bug 类型摘要

### 自定义输出目录

```bash
python3 extract_bug_data.py --output-dir my_output
```

### 查看帮助

```bash
python3 extract_bug_data.py --help
```

## 数据摘要

**总计**: 245 个 bugs，来自 16 个开源项目

### Top 5 项目（按 bug 数量）

1. **llvm___llvm-project** - 143 bugs
2. **danmar___cppcheck** - 32 bugs
3. **CESNET___libyang** - 15 bugs
4. **fmtlib___fmt** - 14 bugs
5. **KhronosGroup___SPIRV-Tools** - 12 bugs

### Top 5 Bug 类型

1. **Logic Organization: Improper Condition Organization** - 66 bugs
2. **Sanitizer: Control Expression Error** - 64 bugs
3. **Signature: Incorrect Variable Usage** - 25 bugs
4. **Logic Organization: Wrong Function Call Sequence** - 20 bugs
5. **Signature: Incorrect Function Return Value** - 19 bugs

## 数据结构

每个 bug 包含以下信息：

- **项目信息**: 项目名称、仓库 URL
- **提交信息**: 修复前后的 commit SHA、提交日期
- **Bug 类型**: bug 类型名称、ID、分类
- **源文件**: 受影响的源代码文件和测试文件
- **函数位置**: bug 所在函数的起始和结束位置
- **测试信息**: 相关的单元测试名称和状态

## 输出格式详解

### all_bugs.json
完整的 JSON 格式数据，包含所有原始字段和项目信息。适合程序化处理。

### all_bugs.csv
适合在 Excel 或其他表格工具中查看和分析的 CSV 格式。包含主要字段的扁平化视图。

### statistics.json
按项目、bug 类型、bug ID 分类的统计信息，包含生成时间戳。

### PROJECT_SUMMARY.md
Markdown 格式的摘要报告，包含项目列表、bug 数量分布和类型统计。

## 使用场景

1. **研究分析**: 分析不同项目和 bug 类型的分布
2. **数据挖掘**: 提取特定类型的 bug 进行深入研究
3. **报告生成**: 快速生成统计报告
4. **工具开发**: 作为其他工具的数据源

## 许可证

本工具遵循与 Defects4C 仓库相同的许可证。
