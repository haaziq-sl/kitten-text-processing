"""Reviewed linguistic examples and independent contact-detail contracts."""
import os
import unittest

from kitten_text_processing.voice import VoiceNormalizer, VOICE_LANGUAGES


@unittest.skipUnless(os.environ.get('KITTEN_VOICE_NORMALIZATION_LIBRARY'), 'optional C++ voice backend')
class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = VoiceNormalizer()
        cls.n.warm()

    def test_reviewed_recordings(self):
        examples = [
            ('ar', 'ضبطت المنبه على الساعة 9:30 PM.', 'ضبطت المنبه على الساعة التاسعة والنصف مساءً.'),
            ('zh', '总金额是USD 1,234.56。', '总金额是一千二百三十四美元五十六美分。'),
            ('nl', 'De klok geeft 14:05:09 aan.', 'De klok geeft veertien uur vijf minuten en negen seconden aan.'),
            ('fr', 'L’horloge indique 14:05:09.', 'L’horloge indique quatorze heures cinq minutes et neuf secondes.'),
            ('de', 'Die Uhr zeigt 14:05:09 an.', 'Die Uhr zeigt vierzehn Uhr fünf Minuten und neun Sekunden an.'),
            ('id', 'Harga tiketnya Rp12.500,50.', 'Harga tiketnya dua belas ribu lima ratus rupiah lima puluh sen.'),
            ('ko', '총금액은 USD 1,234.56입니다.', '총금액은 천이백삼십사 달러 오십육 센트입니다.'),
            ('ko', '기차는 14:05에 출발합니다.', '기차는 십사 시 오 분에 출발합니다.'),
            ('ko', '시계는 14:05:09를 가리킵니다.', '시계는 십사 시 오 분 구 초를 가리킵니다.'),
            ('ru', 'Общая сумма составляет 1 234,56 USD.', 'Общая сумма составляет тысячу двести тридцать четыре доллара США и пятьдесят шесть центов.'),
            ('es', 'El reloj marca las 14:05:09.', 'El reloj marca las catorce horas, cinco minutos y nueve segundos.'),
        ]
        for lang, text, expected in examples:
            with self.subTest(lang=lang, text=text):
                self.assertEqual(self.n.normalize(text, lang), expected)

    def test_related_amount_and_clock_boundaries(self):
        self.assertEqual(self.n.normalize('Rp1,00', 'id'), 'satu rupiah')
        self.assertEqual(self.n.normalize('Rp12.500,5', 'id'), 'dua belas ribu lima ratus rupiah lima puluh sen')
        self.assertEqual(self.n.normalize('Rp0,005', 'id'), 'nol koma nol nol lima rupiah')
        self.assertEqual(self.n.normalize('CNY 1.56', 'zh'), '一元五角六分')
        self.assertEqual(self.n.normalize('14:01:01', 'fr'), 'quatorze heures une minute et une seconde')
        self.assertEqual(self.n.normalize('14:01:01', 'de'), 'vierzehn Uhr eine Minute und eine Sekunde')
        self.assertEqual(self.n.normalize('14:01:01', 'es'), 'catorce horas, un minuto y un segundo')
        self.assertEqual(self.n.normalize('12:00 AM', 'ar'), 'الثانية عشرة ليلًا')
        self.assertEqual(self.n.normalize('12:00 PM', 'ar'), 'الثانية عشرة ظهرًا')
        self.assertEqual(self.n.normalize('9:30 PM', 'ko'), '오후 아홉 시 삼십 분')
        self.assertEqual(self.n.normalize('составляет 21 234 USD', 'ru'),
                         'составляет двадцать одну тысячу двести тридцать четыре доллара США')
        self.assertIn('одна тысяча', self.n.normalize('Баланс: 1 234 USD', 'ru'))
        self.assertIn('составляет\uffff1', self.n.prepare_for_segmentation('Сумма составляет 1 234 USD', 'ru'))

    def test_email_in_every_language(self):
        wording = {
            'en': ('one two', 'at', 'dot'), 'ar': ('واحد اثنان', 'آت', 'نقطة'),
            'zh': ('一 二', '艾特', '点'), 'nl': ('een twee', 'apenstaartje', 'punt'),
            'fr': ('un deux', 'arobase', 'point'), 'de': ('eins zwei', 'ät', 'Punkt'),
            'hi': ('एक दो', 'ऐट', 'डॉट'), 'id': ('satu dua', 'at', 'titik'),
            'it': ('uno due', 'chiocciola', 'punto'), 'ja': ('一 二', 'アットマーク', 'ドット'),
            'ko': ('일 이', '골뱅이', '점'), 'pl': ('jeden dwa', 'małpa', 'kropka'),
            'pt': ('um dois', 'arroba', 'ponto'), 'ru': ('один два', 'собака', 'точка'),
            'es': ('uno dos', 'arroba', 'punto'), 'tr': ('bir iki', 'et', 'nokta'),
        }
        self.assertEqual(set(wording), set(VOICE_LANGUAGES))
        for lang, (digits, at, dot) in wording.items():
            with self.subTest(lang=lang):
                self.assertEqual(self.n.normalize('user12@gmail.com', lang),
                                 f'user {digits} {at} gmail {dot} com')
                self.assertEqual(self.n.normalize('user@gmail.com', lang),
                                 f'user {at} gmail {dot} com')

    def test_phone_and_url_identity(self):
        self.assertEqual(self.n.normalize('+1 (202) 555-0123 x45', 'en'),
                         'plus one, two zero two, five five five, zero one two three extension four five')
        self.assertEqual(self.n.normalize('123 456 7890', 'en'),
                         'one two three, four five six, seven eight nine zero')
        self.assertEqual(self.n.normalize('Phone: 2025550123', 'en'),
                         'Phone: two zero two five five five zero one two three')
        self.assertEqual(self.n.normalize('फोन: +919876543210', 'hi'),
                         'फोन: प्लस नौ एक नौ आठ सात छह पाँच चार तीन दो एक शून्य')
        self.assertEqual(self.n.normalize('Email ana.smith_12+news@gmail.com.', 'en'),
                         'Email ana dot smith underscore one two plus news at gmail dot com.')
        self.assertEqual(self.n.normalize('example.com/a12?x=0.5', 'en'),
                         'example dot com slash a one two question mark x equals zero dot five')
        self.assertEqual(self.n.normalize('https://example.com/docs', 'en'),
                         'H T T P S colon slash slash example dot com slash docs')
        self.assertEqual(self.n.normalize('HTTPS://example.com/docs', 'en'),
                         'H T T P S colon slash slash example dot com slash docs')
        self.assertEqual(self.n.normalize('1 234 567', 'en'), 'one million two hundred thirty-four thousand five hundred sixty-seven')
        self.assertEqual(self.n.normalize('123.com/path12', 'en'),
                         'one two three dot com slash path one two')
        self.assertEqual(self.n.normalize('9.63% 3.14159', 'en'),
                         'nine point six three percent three point one four one five nine')

    def test_contacts_are_idempotent_and_protected_types_stay_protected(self):
        for lang in VOICE_LANGUAGES:
            for text in ['ana.smith_12+news@gmail.com', 'example.com/a12?x=0.5',
                         'https://example.com/a%20b#item12', '+1 (202) 555-0123 x45',
                         '123 456 7890', 'PIN: 12']:
                with self.subTest(lang=lang, text=text):
                    once = self.n.normalize(text, lang)
                    self.assertEqual(self.n.normalize(once, lang), once)
            for text in ['AB12.34', 'v1.2.3', '192.168.1.2', '1e-10', 'x123',
                         '1990s3.5', '1,000v0.8', '2027v1.2', r'C:\a12@b.txt']:
                with self.subTest(lang=lang, text=text):
                    self.assertEqual(self.n.normalize(text, lang), text)


if __name__ == '__main__':
    unittest.main()
