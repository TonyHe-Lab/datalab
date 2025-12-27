#!/usr/bin/env python3
"""
ETL 命令行入口点
"""

import sys
import os

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.etl.incremental_sync import main

if __name__ == "__main__":
    main()
