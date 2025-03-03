from .fragranticaspider import FragranticaSpider


class FragranticarabiaSpider(FragranticaSpider):
    name = 'fragranticarabia'
    base_url = 'https://www.fragranticarabia.com/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.language_character = 'AR'
