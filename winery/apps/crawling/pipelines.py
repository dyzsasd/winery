from winery.apps.crawling.extractors.vivino.crawling import *


class VivinoPipeline(object):
    def process_item(self, item, spider):
        components = item['url'].split('/')
        if len(components) > 3:
            rub = components[3]
            task = None
            if rub == 'wine-countries':
                task = CountryTask(item['url'], item['content'])
            elif rub == 'wine-regions':
                task = RegionTask(item['url'], item['content'])
            elif rub == 'wineries':
                if len(components) > 5 and components[5] == 'wines':
                    task = WinTask(item['url'], item['content'])
                else:
                    task = WineryTask(item['url'], item['content'])
            elif rub == 'grapes':
                task = GrapTask(item['url'], item['content'])
            elif rub == 'wine-styles':
                task = RegionStyleTask(item['url'], item['content'])
        if task:
            document = task.parse()
            document.save()
            item['content'] = 'processed and saved'
        else:
            item['content'] = 'error'
        return item
