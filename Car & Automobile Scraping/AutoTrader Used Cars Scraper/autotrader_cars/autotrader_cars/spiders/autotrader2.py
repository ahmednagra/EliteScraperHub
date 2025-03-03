from .autotrader1 import AutotraderSpider


class AutotraderSpider2(AutotraderSpider):
    name = 'autotrader2'

    def parse(self, response, **kwargs):
        makes = self.get_makes_names(response)
        self.makes = makes[35:]
