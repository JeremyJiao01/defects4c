#!/bin/bash
# 打包 Defects4C 训练数据集

set -e

echo "======================================================================"
echo "Defects4C 数据集打包工具"
echo "======================================================================"
echo ""

DATASET_DIR="bug_source_code"
OUTPUT_FILE="defects4c_dataset_$(date +%Y%m%d).tar.gz"

# 检查数据集目录是否存在
if [ ! -d "$DATASET_DIR" ]; then
    echo "错误: 数据集目录 '$DATASET_DIR' 不存在"
    echo "请先运行: python3 extract_bug_source_code.py"
    exit 1
fi

# 统计信息
echo "数据集信息:"
echo "  - 位置: $DATASET_DIR"
echo "  - 大小: $(du -sh $DATASET_DIR | cut -f1)"
echo "  - Bug 数量: $(find $DATASET_DIR/source_files -maxdepth 1 -type d | tail -n +2 | wc -l)"
echo ""

# 开始打包
echo "开始打包..."
tar -czf "$OUTPUT_FILE" \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    "$DATASET_DIR/metadata.json" \
    "$DATASET_DIR/source_files/" \
    "$DATASET_DIR/diffs/" \
    "$DATASET_DIR/functions/" \
    "$DATASET_DIR/EXTRACTION_REPORT.md"

# 打包完成
if [ -f "$OUTPUT_FILE" ]; then
    COMPRESSED_SIZE=$(du -sh "$OUTPUT_FILE" | cut -f1)
    echo ""
    echo "✅ 打包完成!"
    echo "  - 输出文件: $OUTPUT_FILE"
    echo "  - 压缩后大小: $COMPRESSED_SIZE"
    echo ""
    echo "使用方法:"
    echo "  1. 传输到目标机器: scp $OUTPUT_FILE user@host:/path/"
    echo "  2. 解压: tar -xzf $OUTPUT_FILE"
    echo "  3. 查看使用指南: cat DATASET_USAGE_GUIDE.md"
    echo ""
else
    echo "❌ 打包失败"
    exit 1
fi

# 生成 SHA256 校验和
echo "生成校验和..."
sha256sum "$OUTPUT_FILE" > "${OUTPUT_FILE}.sha256"
echo "  - 校验文件: ${OUTPUT_FILE}.sha256"
echo ""

echo "======================================================================"
echo "全部完成!"
echo "======================================================================"
