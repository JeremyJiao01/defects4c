# Defects4C 训练数据集使用指南

## 📦 数据集概览

成功提取了 **245 个真实 C/C++ bug** 的完整源代码，来自 16 个知名开源项目。

### 数据集规模

- **总大小**: 88 MB
- **Bug 数量**: 245 个
- **源文件**: 490 个 (.c 文件，包含 buggy 和 fixed 版本)
- **Diff 文件**: 245 个
- **函数代码**: 490 个（提取的 bug 函数片段）
- **项目**: 16 个
- **成功率**: 100%

### 项目分布

| 项目 | Bug 数量 | 占比 |
|------|----------|------|
| llvm-project | 143 | 58.4% |
| cppcheck | 32 | 13.1% |
| libyang | 15 | 6.1% |
| fmt | 14 | 5.7% |
| SPIRV-Tools | 12 | 4.9% |
| arrow | 9 | 3.7% |
| 其他 10 个项目 | 20 | 8.1% |

## 🗂️ 数据集结构

```
bug_source_code/                    # 主目录 (88MB)
│
├── metadata.json                   # 核心元数据文件
│   └── 包含所有 245 个 bug 的详细信息
│
├── source_files/                   # 完整源代码 (按 bug 组织)
│   ├── {project}_{index}_{commit}/
│   │   ├── buggy.c                 # 修复前的完整源文件
│   │   └── fixed.c                 # 修复后的完整源文件
│   └── ... (245 个目录)
│
├── diffs/                          # Unified diff 格式
│   ├── {bug_id}.diff               # 修复的具体变化
│   └── ... (245 个文件)
│
├── functions/                      # 函数级别代码片段
│   ├── {bug_id}/
│   │   ├── buggy_function.c        # 包含 bug 的函数
│   │   └── fixed_function.c        # 修复后的函数
│   └── ... (245 个目录)
│
└── EXTRACTION_REPORT.md            # 提取报告
```

## 📋 元数据格式 (metadata.json)

每个 bug 条目包含以下字段：

```json
{
  "bug_id": "CESNET___libyang_1_09abf888",
  "bug_index": 1,
  "project_name": "CESNET___libyang",
  "repository": "CESNET/libyang",
  "bug_type": "Logic Organization: Improper Condition Organization",
  "bug_type_id": "D.1",
  "commit_before": "09abf888c0f33904f05d2c93c4465a92927fd500",
  "commit_after": "ea0f96cf45deed39fb98b28f30d0acdc304db243",
  "commit_date": "2022-12-20T07:48:33Z",
  "file_path": "src/printer_xml.c",
  "all_src_files": ["src/printer_xml.c"],
  "test_files": ["tests/utests/data/test_new.c"],
  "location": {
    "func_start": 287,
    "func_end": 294,
    "hunk_start": 287,
    "hunk_end": 294
  },
  "files": {
    "buggy_full": "source_files/CESNET___libyang_1_09abf888/buggy.c",
    "fixed_full": "source_files/CESNET___libyang_1_09abf888/fixed.c",
    "diff": "diffs/CESNET___libyang_1_09abf888.diff",
    "buggy_function": "functions/CESNET___libyang_1_09abf888/buggy_function.c",
    "fixed_function": "functions/CESNET___libyang_1_09abf888/fixed_function.c"
  },
  "stats": {
    "buggy_lines": 602,
    "fixed_lines": 604,
    "function_lines": 8
  }
}
```

### 关键字段说明

- **bug_id**: 唯一标识符，格式为 `{project}_{index}_{commit_sha[:8]}`
- **bug_type_id**: Bug 分类 ID (A.1-A.4, B, C.1-C.3, D.1-D.2)
- **location**: Bug 在源文件中的精确位置（行号）
- **files**: 所有相关文件的相对路径
- **stats**: 代码行数统计

## 🚀 快速开始

### 1. 打包数据集（离线传输）

```bash
# 打包整个数据集
tar -czf defects4c_dataset.tar.gz bug_source_code/

# 查看压缩后大小
ls -lh defects4c_dataset.tar.gz

# 解压（在目标机器上）
tar -xzf defects4c_dataset.tar.gz
```

### 2. Python 加载示例

```python
import json
from pathlib import Path

# 加载元数据
def load_dataset(dataset_dir='bug_source_code'):
    metadata_file = Path(dataset_dir) / 'metadata.json'
    with open(metadata_file, 'r') as f:
        return json.load(f)

# 读取特定 bug 的源码
def load_bug_source(bug, dataset_dir='bug_source_code'):
    buggy_path = Path(dataset_dir) / bug['files']['buggy_full']
    fixed_path = Path(dataset_dir) / bug['files']['fixed_full']

    with open(buggy_path, 'r') as f:
        buggy_code = f.read()

    with open(fixed_path, 'r') as f:
        fixed_code = f.read()

    return buggy_code, fixed_code

# 使用示例
bugs = load_dataset()
print(f"加载了 {len(bugs)} 个 bugs")

# 获取第一个 bug
bug = bugs[0]
print(f"\nBug ID: {bug['bug_id']}")
print(f"项目: {bug['project_name']}")
print(f"类型: {bug['bug_type_id']} - {bug['bug_type']}")

# 加载源码
buggy, fixed = load_bug_source(bug)
print(f"\nBuggy 代码: {len(buggy)} 字符")
print(f"Fixed 代码: {len(fixed)} 字符")
```

### 3. 过滤和筛选

```python
# 按 bug 类型过滤
def filter_by_type(bugs, bug_type_id):
    return [b for b in bugs if b['bug_type_id'] == bug_type_id]

# 按项目过滤
def filter_by_project(bugs, project_name):
    return [b for b in bugs if b['project_name'] == project_name]

# 示例：获取所有内存错误类型的 bug
bugs = load_dataset()
memory_bugs = [b for b in bugs if b['bug_type_id'].startswith('C.')]
print(f"内存错误 bugs: {len(memory_bugs)} 个")

# 获取所有 llvm 项目的 bugs
llvm_bugs = filter_by_project(bugs, 'llvm___llvm-project')
print(f"LLVM bugs: {len(llvm_bugs)} 个")
```

## 🧠 训练用例

### 用例 1: Bug 分类模型

训练一个模型来识别代码中的 bug 类型。

```python
import json
from pathlib import Path

def prepare_classification_data(dataset_dir='bug_source_code'):
    bugs = load_dataset(dataset_dir)

    X = []  # 特征 (buggy code)
    y = []  # 标签 (bug_type_id)

    for bug in bugs:
        buggy_code, _ = load_bug_source(bug, dataset_dir)
        X.append(buggy_code)
        y.append(bug['bug_type_id'])

    return X, y

# 加载数据
X, y = prepare_classification_data()
print(f"训练样本: {len(X)}")
print(f"类别分布: {set(y)}")
```

### 用例 2: Bug 修复生成模型

训练一个模型来自动修复 bug。

```python
def prepare_bug_fix_data(dataset_dir='bug_source_code'):
    bugs = load_dataset(dataset_dir)

    data = []
    for bug in bugs:
        # 读取完整文件
        buggy_code, fixed_code = load_bug_source(bug, dataset_dir)

        # 或者只读取函数级别的代码
        func_dir = Path(dataset_dir) / 'functions' / bug['bug_id']
        if (func_dir / 'buggy_function.c').exists():
            with open(func_dir / 'buggy_function.c', 'r') as f:
                buggy_func = f.read()
            with open(func_dir / 'fixed_function.c', 'r') as f:
                fixed_func = f.read()

            data.append({
                'bug_id': bug['bug_id'],
                'buggy': buggy_func,
                'fixed': fixed_func,
                'bug_type': bug['bug_type_id'],
                'location': bug['location']
            })

    return data

# 加载数据
fix_data = prepare_bug_fix_data()
print(f"Bug 修复样本: {len(fix_data)}")
```

### 用例 3: Diff 分析

分析 bug 修复的模式。

```python
def load_diffs(dataset_dir='bug_source_code'):
    bugs = load_dataset(dataset_dir)
    diffs = []

    for bug in bugs:
        diff_file = Path(dataset_dir) / bug['files']['diff']
        with open(diff_file, 'r') as f:
            diff_content = f.read()

        diffs.append({
            'bug_id': bug['bug_id'],
            'bug_type': bug['bug_type_id'],
            'diff': diff_content,
            'project': bug['project_name']
        })

    return diffs

# 示例：分析不同类型 bug 的修复行数
diffs = load_diffs()
for bug_type in ['A.1', 'B', 'C.1', 'D.1']:
    type_diffs = [d for d in diffs if d['bug_type'] == bug_type]
    avg_lines = sum(len(d['diff'].split('\n')) for d in type_diffs) / len(type_diffs)
    print(f"{bug_type}: 平均 {avg_lines:.1f} 行修改")
```

## 📊 数据集统计

### Bug 类型分布

| ID | 类型 | 数量 | 占比 |
|----|------|------|------|
| D.1 | Logic: Improper Condition | 66 | 26.9% |
| B | Sanitizer: Control Expression Error | 64 | 26.1% |
| A.4 | Signature: Incorrect Variable | 25 | 10.2% |
| D.2 | Logic: Wrong Call Sequence | 20 | 8.2% |
| A.3 | Signature: Incorrect Return | 19 | 7.8% |
| A.1 | Signature: Incorrect Function | 19 | 7.8% |
| A.2 | Signature: Fault Input Type | 12 | 4.9% |
| C.2 | Memory: Resource Consumption | 9 | 3.7% |
| C.1 | Memory: Null Pointer | 6 | 2.4% |
| C.3 | Memory: Overflow | 5 | 2.0% |

详细分类说明请参考 `BUG_TYPE_CLASSIFICATION.md`

## 🔧 高级用法

### 构建训练/测试集

```python
from sklearn.model_selection import train_test_split

bugs = load_dataset()

# 按 8:2 划分训练/测试集
train_bugs, test_bugs = train_test_split(bugs, test_size=0.2, random_state=42)

print(f"训练集: {len(train_bugs)} bugs")
print(f"测试集: {len(test_bugs)} bugs")

# 确保测试集包含所有 bug 类型
test_types = set(b['bug_type_id'] for b in test_bugs)
print(f"测试集覆盖的 bug 类型: {len(test_types)}")
```

### 代码 Tokenization

```python
# 示例：使用 tree-sitter 进行 C/C++ 代码解析
# pip install tree-sitter tree-sitter-cpp

from tree_sitter import Language, Parser

def parse_code(code, language='cpp'):
    # 需要先构建 tree-sitter language
    parser = Parser()
    # parser.set_language(Language('build/my-languages.so', 'cpp'))
    # tree = parser.parse(bytes(code, 'utf8'))
    # return tree
    pass

# 提取 AST 特征用于训练
```

### 数据增强

```python
# 示例：通过变量重命名进行数据增强
import re

def rename_variables(code, mapping):
    """简单的变量重命名（实际应用中需要使用 AST）"""
    for old_name, new_name in mapping.items():
        code = re.sub(r'\b' + old_name + r'\b', new_name, code)
    return code

# 生成更多训练样本
```

## 📝 使用建议

1. **分层采样**: llvm 项目占 58%，建议在训练时进行分层采样以平衡数据
2. **函数级别训练**: 如果只关注 bug 位置，可以只使用 `functions/` 目录下的函数片段
3. **类型平衡**: D.1 和 B 类型占 53%，考虑对少数类进行过采样
4. **交叉验证**: 建议按项目进行交叉验证，测试模型的泛化能力

## 🔗 相关文件

- `BUG_DATA_README.md` - Bug 数据提取工具使用说明
- `BUG_TYPE_CLASSIFICATION.md` - Bug 类型详细分类说明
- `bug_source_code/EXTRACTION_REPORT.md` - 提取报告
- `extract_bug_source_code.py` - 源码提取脚本

## 📄 引用

如果使用这个数据集，请引用 Defects4C 原始论文：

```bibtex
@inproceedings{defects4c,
  title={Defects4C: A Benchmark for Bugs in C/C++ Programs},
  year={2024}
}
```

## ⚠️ 注意事项

1. **许可证**: 所有源码遵循原项目的开源许可证
2. **研究用途**: 本数据集仅供学术研究和教育使用
3. **版本**: 源码基于特定 commit，可能与最新版本有差异
4. **完整性**: 某些 bug 可能需要完整的项目上下文才能理解

## 🆘 常见问题

**Q: 数据集太大了怎么办？**
A: 可以只使用 `functions/` 目录（函数级别代码）或按项目/类型筛选

**Q: 如何验证数据集的完整性？**
A: 检查 `metadata.json` 应该包含 245 个条目，每个 bug 应该有对应的文件

**Q: 可以重新提取源码吗？**
A: 可以，运行 `python extract_bug_source_code.py` 即可重新从 GitHub 提取

**Q: 如何处理不同项目的编译差异？**
A: 建议使用原始项目的 `project.json` 中的编译配置信息

---

**数据集生成时间**: 2026-01-17
**提取成功率**: 100% (245/245)
**数据集版本**: 1.0
