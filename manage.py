#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "winery.settings")

    from django.core.management import execute_from_command_line
    
    if len(sys.argv) >= 3 and sys.argv[1] == 'crawl':
        if sys.argv[2] == 'vivino':
            from winery.apps.vivinocrawler.crawling import main
            main()
    else:
        execute_from_command_line(sys.argv)
