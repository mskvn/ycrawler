import unittest

from ycrawler import find_news_items, find_link_from_comments


class YcrawlerTest(unittest.TestCase):

    def test_find_news_items(self):
        with open('main_page_test.html') as f:
            html = f.read()
        news_items = find_news_items(html)
        self.assertEqual(len(news_items), 30)
        self.assertEqual(news_items[0].get('id'), '24964800')

    def test_find_link_from_comments(self):
        with open('comments_page_test.html') as f:
            html = f.read()
        links = find_link_from_comments(html)
        self.assertIsInstance(links, dict)
        self.assertTrue(links)
        self.assertTrue('24965408_0' in links)
        self.assertTrue('http' in links['24965408_0'])
