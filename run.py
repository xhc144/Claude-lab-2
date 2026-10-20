"""启动 Folio：python run.py [文件.pdf ...]"""
import sys

from folio.app import main

if __name__ == "__main__":
    sys.exit(main())
