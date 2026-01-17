#!/usr/bin/env python3
"""
Bug 源代码提取工具
从 GitHub 提取所有 bug 的源代码（修复前后版本）

Usage:
    python extract_bug_source_code.py [--output-dir OUTPUT_DIR] [--limit LIMIT]
"""

import json
import os
import re
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import argparse
import difflib


class SourceCodeExtractor:
    """源代码提取器"""

    def __init__(self, output_dir="bug_source_code", use_cache=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.use_cache = use_cache
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'cached': 0
        }

        # 创建子目录
        (self.output_dir / 'source_files').mkdir(exist_ok=True)
        (self.output_dir / 'diffs').mkdir(exist_ok=True)
        (self.output_dir / 'functions').mkdir(exist_ok=True)

    def parse_github_url(self, repo_url):
        """从 GitHub URL 中提取 owner 和 repo 名称"""
        # 处理各种格式的 GitHub URL
        patterns = [
            r'github\.com/([^/]+)/([^/\.]+)',
            r'github\.com/repos/([^/]+)/([^/]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, repo_url)
            if match:
                return match.group(1), match.group(2).replace('.git', '')

        return None, None

    def fetch_file_from_github(self, owner, repo, commit, file_path, max_retries=3):
        """从 GitHub 获取指定 commit 的文件内容"""
        # 使用 raw.githubusercontent.com
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{commit}/{file_path}"

        for attempt in range(max_retries):
            try:
                # 添加 User-Agent 避免被拒绝
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=10) as response:
                    content = response.read().decode('utf-8')
                    return content
            except HTTPError as e:
                if e.code == 404:
                    print(f"      ⚠ 文件未找到: {file_path}")
                    return None
                elif e.code == 403:
                    print(f"      ⚠ 访问被拒绝 (可能是 API 限制), 等待 {2 ** attempt} 秒...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"      ⚠ HTTP 错误 {e.code}: {e.reason}")
                    return None
            except URLError as e:
                print(f"      ⚠ 网络错误: {e.reason}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except Exception as e:
                print(f"      ⚠ 未知错误: {str(e)}")
                return None

        return None

    def extract_function_code(self, content, func_start, func_end):
        """根据行号提取函数代码"""
        if not content or func_start is None or func_end is None:
            return None

        lines = content.split('\n')
        if func_start < 1 or func_end > len(lines):
            return None

        # 行号从 1 开始，列表索引从 0 开始
        func_lines = lines[func_start - 1:func_end]
        return '\n'.join(func_lines)

    def generate_diff(self, content_before, content_after):
        """生成两个版本之间的 diff"""
        if not content_before or not content_after:
            return None

        diff = difflib.unified_diff(
            content_before.splitlines(keepends=True),
            content_after.splitlines(keepends=True),
            fromfile='buggy',
            tofile='fixed',
            lineterm=''
        )
        return ''.join(diff)

    def extract_bug_source(self, bug, bug_index):
        """提取单个 bug 的源代码"""
        project_name = bug.get('project_name', 'unknown')
        commit_before = bug.get('commit_before')
        commit_after = bug.get('commit_after')
        repo_url = bug.get('project_info', {}).get('main_repo', '')

        # 解析仓库信息
        owner, repo = self.parse_github_url(repo_url)
        if not owner or not repo:
            print(f"  ⚠ 无法解析仓库 URL: {repo_url}")
            return None

        # 获取源文件列表
        src_files = bug.get('files', {}).get('src', [])
        if not src_files:
            print(f"  ⚠ 没有源文件信息")
            return None

        # 主要源文件（第一个）
        main_src_file = src_files[0]

        # 生成唯一的 bug ID
        bug_id = f"{project_name}_{bug_index}_{commit_before[:8]}"

        print(f"  提取: {bug_id}")
        print(f"    仓库: {owner}/{repo}")
        print(f"    文件: {main_src_file}")

        # 获取修复前的源码
        print(f"    获取 buggy 版本 ({commit_before[:8]})...", end='')
        content_before = self.fetch_file_from_github(owner, repo, commit_before, main_src_file)
        if content_before:
            print(" ✓")
        else:
            print(" ✗")
            self.stats['failed'] += 1
            return None

        # 获取修复后的源码
        print(f"    获取 fixed 版本 ({commit_after[:8]})...", end='')
        content_after = self.fetch_file_from_github(owner, repo, commit_after, main_src_file)
        if content_after:
            print(" ✓")
        else:
            print(" ✗")
            self.stats['failed'] += 1
            return None

        # 生成 diff
        diff_content = self.generate_diff(content_before, content_after)

        # 提取函数代码（如果有位置信息）
        src_location = bug.get('files', {}).get('src0_location', {})
        func_start = src_location.get('func_start')
        func_end = src_location.get('func_end')

        func_before = self.extract_function_code(content_before, func_start, func_end)
        func_after = self.extract_function_code(content_after, func_start, func_end)

        # 保存文件
        bug_dir = self.output_dir / 'source_files' / bug_id
        bug_dir.mkdir(exist_ok=True)

        # 保存完整源文件
        (bug_dir / 'buggy.c').write_text(content_before, encoding='utf-8')
        (bug_dir / 'fixed.c').write_text(content_after, encoding='utf-8')

        # 保存 diff
        if diff_content:
            (self.output_dir / 'diffs' / f'{bug_id}.diff').write_text(diff_content, encoding='utf-8')

        # 保存函数代码
        if func_before and func_after:
            func_dir = self.output_dir / 'functions' / bug_id
            func_dir.mkdir(exist_ok=True)
            (func_dir / 'buggy_function.c').write_text(func_before, encoding='utf-8')
            (func_dir / 'fixed_function.c').write_text(func_after, encoding='utf-8')

        # 构建结果数据
        result = {
            'bug_id': bug_id,
            'bug_index': bug_index,
            'project_name': project_name,
            'repository': f"{owner}/{repo}",
            'bug_type': bug.get('type', {}).get('name', 'Unknown'),
            'bug_type_id': bug.get('type', {}).get('id', 'Unknown'),
            'commit_before': commit_before,
            'commit_after': commit_after,
            'commit_date': bug.get('commit_date'),
            'file_path': main_src_file,
            'all_src_files': src_files,
            'test_files': bug.get('files', {}).get('test', []),
            'location': {
                'func_start': func_start,
                'func_end': func_end,
                'hunk_start': src_location.get('hunk_start'),
                'hunk_end': src_location.get('hunk_end')
            },
            'files': {
                'buggy_full': f'source_files/{bug_id}/buggy.c',
                'fixed_full': f'source_files/{bug_id}/fixed.c',
                'diff': f'diffs/{bug_id}.diff',
                'buggy_function': f'functions/{bug_id}/buggy_function.c' if func_before else None,
                'fixed_function': f'functions/{bug_id}/fixed_function.c' if func_after else None
            },
            'stats': {
                'buggy_lines': len(content_before.split('\n')),
                'fixed_lines': len(content_after.split('\n')),
                'function_lines': func_end - func_start + 1 if func_start and func_end else None
            }
        }

        self.stats['success'] += 1
        return result

    def extract_all(self, bugs_file, limit=None):
        """提取所有 bug 的源代码"""
        print(f"读取 bug 数据: {bugs_file}")
        with open(bugs_file, 'r', encoding='utf-8') as f:
            bugs = json.load(f)

        if limit:
            bugs = bugs[:limit]
            print(f"限制提取数量: {limit}")

        self.stats['total'] = len(bugs)
        print(f"总共 {len(bugs)} 个 bugs\n")

        results = []
        for i, bug in enumerate(bugs, 1):
            print(f"\n[{i}/{len(bugs)}] 处理 bug...")
            result = self.extract_bug_source(bug, i)
            if result:
                results.append(result)

            # 避免过于频繁的请求
            if i % 10 == 0:
                print(f"\n  暂停 2 秒避免 API 限制...")
                time.sleep(2)

        # 保存元数据
        metadata_file = self.output_dir / 'metadata.json'
        print(f"\n保存元数据到: {metadata_file}")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # 生成统计报告
        self.generate_report(results)

        return results

    def generate_report(self, results):
        """生成提取报告"""
        report_file = self.output_dir / 'EXTRACTION_REPORT.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Bug 源代码提取报告\n\n")
            f.write(f"提取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## 统计信息\n\n")
            f.write(f"- 总 Bug 数: {self.stats['total']}\n")
            f.write(f"- 成功提取: {self.stats['success']}\n")
            f.write(f"- 提取失败: {self.stats['failed']}\n")
            f.write(f"- 成功率: {self.stats['success'] / self.stats['total'] * 100:.1f}%\n\n")

            f.write("## 数据集结构\n\n")
            f.write("```\n")
            f.write("bug_source_code/\n")
            f.write("├── metadata.json              # 所有 bug 的元数据\n")
            f.write("├── source_files/              # 完整源文件\n")
            f.write("│   └── {bug_id}/\n")
            f.write("│       ├── buggy.c            # 修复前的源码\n")
            f.write("│       └── fixed.c            # 修复后的源码\n")
            f.write("├── diffs/                     # Unified diff 文件\n")
            f.write("│   └── {bug_id}.diff\n")
            f.write("├── functions/                 # 函数级别代码（如果有位置信息）\n")
            f.write("│   └── {bug_id}/\n")
            f.write("│       ├── buggy_function.c\n")
            f.write("│       └── fixed_function.c\n")
            f.write("└── EXTRACTION_REPORT.md       # 本报告\n")
            f.write("```\n\n")

            f.write("## 按项目统计\n\n")
            project_stats = {}
            for result in results:
                project = result['project_name']
                project_stats[project] = project_stats.get(project, 0) + 1

            f.write("| 项目 | Bug 数量 |\n")
            f.write("|------|----------|\n")
            for project, count in sorted(project_stats.items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {project} | {count} |\n")

            f.write("\n## 按 Bug 类型统计\n\n")
            type_stats = {}
            for result in results:
                bug_type = result['bug_type_id']
                type_stats[bug_type] = type_stats.get(bug_type, 0) + 1

            f.write("| Bug 类型 ID | 数量 |\n")
            f.write("|-------------|------|\n")
            for bug_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {bug_type} | {count} |\n")

            f.write("\n## 使用说明\n\n")
            f.write("### 训练数据格式\n\n")
            f.write("`metadata.json` 包含所有 bug 的详细信息，每个条目包括：\n\n")
            f.write("- **bug_id**: 唯一标识符\n")
            f.write("- **bug_type_id**: bug 类型 (A.1-A.4, B, C.1-C.3, D.1-D.2)\n")
            f.write("- **files**: 源码文件的相对路径\n")
            f.write("- **location**: bug 在源文件中的位置（行号）\n")
            f.write("- **repository**: GitHub 仓库\n\n")

            f.write("### 离线使用\n\n")
            f.write("整个 `bug_source_code/` 目录可以直接打包用于离线训练：\n\n")
            f.write("```bash\n")
            f.write("tar -czf bug_dataset.tar.gz bug_source_code/\n")
            f.write("```\n\n")

            f.write("### 加载数据示例 (Python)\n\n")
            f.write("```python\n")
            f.write("import json\n\n")
            f.write("# 读取元数据\n")
            f.write("with open('bug_source_code/metadata.json', 'r') as f:\n")
            f.write("    bugs = json.load(f)\n\n")
            f.write("# 访问第一个 bug\n")
            f.write("bug = bugs[0]\n")
            f.write("print(f\"Bug ID: {bug['bug_id']}\")\n")
            f.write("print(f\"Type: {bug['bug_type_id']}\")\n\n")
            f.write("# 读取源代码\n")
            f.write("buggy_file = f\"bug_source_code/{bug['files']['buggy_full']}\"\n")
            f.write("with open(buggy_file, 'r') as f:\n")
            f.write("    buggy_code = f.read()\n")
            f.write("```\n")

        print(f"\n✅ 报告已保存: {report_file}")


def main():
    parser = argparse.ArgumentParser(description='提取所有 bug 的源代码')
    parser.add_argument('--bugs-file', '-b', default='bug_data_output/all_bugs.json',
                        help='Bug 数据 JSON 文件 (默认: bug_data_output/all_bugs.json)')
    parser.add_argument('--output-dir', '-o', default='bug_source_code',
                        help='输出目录 (默认: bug_source_code)')
    parser.add_argument('--limit', '-l', type=int, default=None,
                        help='限制提取数量（用于测试）')

    args = parser.parse_args()

    extractor = SourceCodeExtractor(output_dir=args.output_dir)

    print("=" * 80)
    print("Bug 源代码提取工具")
    print("=" * 80)
    print()

    results = extractor.extract_all(args.bugs_file, limit=args.limit)

    print("\n" + "=" * 80)
    print("提取完成!")
    print("=" * 80)
    print(f"\n统计:")
    print(f"  总数: {extractor.stats['total']}")
    print(f"  成功: {extractor.stats['success']}")
    print(f"  失败: {extractor.stats['failed']}")
    print(f"  成功率: {extractor.stats['success'] / extractor.stats['total'] * 100:.1f}%")
    print(f"\n输出目录: {args.output_dir}")
    print(f"  - metadata.json: 元数据文件")
    print(f"  - source_files/: 完整源代码文件")
    print(f"  - diffs/: Diff 文件")
    print(f"  - functions/: 函数级别代码")
    print(f"  - EXTRACTION_REPORT.md: 详细报告")


if __name__ == '__main__':
    main()
