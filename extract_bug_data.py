#!/usr/bin/env python3
"""
Defects4C Bug Data Extraction Tool
提取并整合所有项目的 bug 数据

Usage:
    python extract_bug_data.py [--output-dir OUTPUT_DIR]
"""

import json
import csv
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import argparse


class BugDataExtractor:
    """Bug 数据提取器"""

    def __init__(self, base_dir="defectsc_tpl/projects_v1"):
        self.base_dir = Path(base_dir)
        self.all_bugs = []
        self.stats = defaultdict(int)

    def extract_all_bugs(self):
        """提取所有项目的 bug 数据"""
        print(f"正在从 {self.base_dir} 提取 bug 数据...")

        # 遍历所有项目目录
        for project_dir in sorted(self.base_dir.iterdir()):
            if not project_dir.is_dir():
                continue

            # 跳过模板文件
            if project_dir.name.endswith('.jinja') or project_dir.name.endswith('.py'):
                continue

            bugs_file = project_dir / "bugs_list_new.json"
            project_file = project_dir / "project.json"

            if not bugs_file.exists():
                continue

            # 读取项目信息
            project_info = {}
            if project_file.exists():
                with open(project_file, 'r', encoding='utf-8') as f:
                    project_info = json.load(f)

            # 读取 bug 列表
            with open(bugs_file, 'r', encoding='utf-8') as f:
                bugs = json.load(f)

            project_name = project_dir.name
            print(f"  - {project_name}: {len(bugs)} bugs")

            # 为每个 bug 添加项目信息
            for bug in bugs:
                bug['project_name'] = project_name
                bug['project_info'] = project_info
                self.all_bugs.append(bug)

                # 统计
                self.stats['total_bugs'] += 1
                self.stats[f"project_{project_name}"] += 1

                # 按 bug 类型统计
                bug_type = bug.get('type', {}).get('name', 'Unknown')
                self.stats[f"type_{bug_type}"] += 1

                # 按 bug ID 统计
                bug_type_id = bug.get('type', {}).get('id', 'Unknown')
                self.stats[f"type_id_{bug_type_id}"] += 1

        print(f"\n总计: {len(self.all_bugs)} bugs from {self._count_projects()} projects")
        return self.all_bugs

    def _count_projects(self):
        """统计项目数量"""
        projects = set()
        for bug in self.all_bugs:
            projects.add(bug.get('project_name'))
        return len(projects)

    def save_to_json(self, output_file):
        """保存为 JSON 格式"""
        print(f"\n保存到 JSON: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_bugs, f, indent=2, ensure_ascii=False)
        print(f"  ✓ 已保存 {len(self.all_bugs)} 条记录")

    def save_to_csv(self, output_file):
        """保存为 CSV 格式"""
        print(f"\n保存到 CSV: {output_file}")

        if not self.all_bugs:
            print("  ⚠ 没有数据可保存")
            return

        # CSV 字段
        fieldnames = [
            'project_name',
            'commit_after',
            'commit_before',
            'commit_date',
            'bug_type_name',
            'bug_type_id',
            'bug_category',
            'status',
            'url',
            'src_files',
            'test_files',
            'func_start',
            'func_end',
            'test_name',
            'test_status'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for bug in self.all_bugs:
                row = {
                    'project_name': bug.get('project_name', ''),
                    'commit_after': bug.get('commit_after', ''),
                    'commit_before': bug.get('commit_before', ''),
                    'commit_date': bug.get('commit_date', ''),
                    'bug_type_name': bug.get('type', {}).get('name', ''),
                    'bug_type_id': bug.get('type', {}).get('id', ''),
                    'bug_category': bug.get('type', {}).get('type', ''),
                    'status': bug.get('status', ''),
                    'url': bug.get('url', ''),
                    'src_files': '; '.join(bug.get('files', {}).get('src', [])),
                    'test_files': '; '.join(bug.get('files', {}).get('test', [])),
                    'func_start': bug.get('files', {}).get('src0_location', {}).get('func_start', ''),
                    'func_end': bug.get('files', {}).get('src0_location', {}).get('func_end', ''),
                    'test_name': '; '.join(bug.get('unittest', {}).get('name', [])),
                    'test_status': bug.get('unittest', {}).get('status', '')
                }
                writer.writerow(row)

        print(f"  ✓ 已保存 {len(self.all_bugs)} 条记录")

    def save_statistics(self, output_file):
        """保存统计报告"""
        print(f"\n保存统计报告: {output_file}")

        # 按项目统计
        project_stats = defaultdict(int)
        type_stats = defaultdict(int)
        type_id_stats = defaultdict(int)

        for bug in self.all_bugs:
            project_stats[bug.get('project_name', 'Unknown')] += 1
            type_stats[bug.get('type', {}).get('name', 'Unknown')] += 1
            type_id_stats[bug.get('type', {}).get('id', 'Unknown')] += 1

        report = {
            'generated_at': datetime.now().isoformat(),
            'total_bugs': len(self.all_bugs),
            'total_projects': len(project_stats),
            'by_project': dict(sorted(project_stats.items(), key=lambda x: x[1], reverse=True)),
            'by_bug_type': dict(sorted(type_stats.items(), key=lambda x: x[1], reverse=True)),
            'by_bug_type_id': dict(sorted(type_id_stats.items(), key=lambda x: x[1], reverse=True))
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 打印统计摘要
        print("\n" + "="*60)
        print("统计摘要")
        print("="*60)
        print(f"\n总 Bug 数: {report['total_bugs']}")
        print(f"总项目数: {report['total_projects']}\n")

        print("Top 10 项目（按 bug 数量）:")
        for i, (project, count) in enumerate(list(report['by_project'].items())[:10], 1):
            print(f"  {i:2d}. {project:40s} {count:4d} bugs")

        print(f"\nTop 10 Bug 类型:")
        for i, (bug_type, count) in enumerate(list(report['by_bug_type'].items())[:10], 1):
            print(f"  {i:2d}. {bug_type:50s} {count:4d} bugs")

        print("="*60)
        print(f"  ✓ 已保存统计报告")

    def save_project_summary(self, output_file):
        """保存项目摘要（Markdown 格式）"""
        print(f"\n保存项目摘要: {output_file}")

        project_bugs = defaultdict(list)
        for bug in self.all_bugs:
            project_bugs[bug.get('project_name', 'Unknown')].append(bug)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Defects4C Bug 数据摘要\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**总计**: {len(self.all_bugs)} bugs, {len(project_bugs)} projects\n\n")

            f.write("## 项目列表\n\n")
            f.write("| # | 项目名称 | Bug 数量 | 仓库 |\n")
            f.write("|---|----------|----------|------|\n")

            for i, (project, bugs) in enumerate(sorted(project_bugs.items(), key=lambda x: len(x[1]), reverse=True), 1):
                # 从第一个 bug 的 URL 中提取仓库信息
                repo_url = ""
                if bugs and bugs[0].get('url'):
                    url = bugs[0]['url']
                    if 'github.com/repos/' in url:
                        parts = url.split('/repos/')[1].split('/commits/')[0]
                        repo_url = f"https://github.com/{parts}"

                repo_link = f"[Link]({repo_url})" if repo_url else "N/A"
                f.write(f"| {i} | `{project}` | {len(bugs)} | {repo_link} |\n")

            f.write("\n## Bug 类型分布\n\n")

            type_stats = defaultdict(int)
            for bug in self.all_bugs:
                bug_type = bug.get('type', {}).get('name', 'Unknown')
                type_stats[bug_type] += 1

            f.write("| # | Bug 类型 | 数量 |\n")
            f.write("|---|----------|------|\n")

            for i, (bug_type, count) in enumerate(sorted(type_stats.items(), key=lambda x: x[1], reverse=True), 1):
                f.write(f"| {i} | {bug_type} | {count} |\n")

        print(f"  ✓ 已保存项目摘要")


def main():
    parser = argparse.ArgumentParser(description='提取 Defects4C 的所有 bug 数据')
    parser.add_argument('--output-dir', '-o', default='bug_data_output',
                        help='输出目录 (默认: bug_data_output)')
    parser.add_argument('--base-dir', '-b', default='defectsc_tpl/projects_v1',
                        help='项目基础目录 (默认: defectsc_tpl/projects_v1)')

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # 提取数据
    extractor = BugDataExtractor(base_dir=args.base_dir)
    extractor.extract_all_bugs()

    # 保存为多种格式
    extractor.save_to_json(output_dir / 'all_bugs.json')
    extractor.save_to_csv(output_dir / 'all_bugs.csv')
    extractor.save_statistics(output_dir / 'statistics.json')
    extractor.save_project_summary(output_dir / 'PROJECT_SUMMARY.md')

    print(f"\n✅ 所有数据已保存到: {output_dir}")
    print("\n生成的文件:")
    print(f"  - all_bugs.json          : 所有 bug 的完整 JSON 数据")
    print(f"  - all_bugs.csv           : CSV 格式 (可用 Excel 打开)")
    print(f"  - statistics.json        : 统计数据")
    print(f"  - PROJECT_SUMMARY.md     : 项目摘要 (Markdown)")


if __name__ == '__main__':
    main()
