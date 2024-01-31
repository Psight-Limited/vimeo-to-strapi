import json
import unittest

import kartra_api


class TestKartraRoutes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = kartra_api.KartraClient()

    async def test_get_users_memberships(self):
        r = await self.client.get_users_memberships("noahlykins@gmail.com")
        self.assertIsInstance(r, list)
        for i in r:
            self.assertIsInstance(i, str)

    async def test_get_tags(self):
        r = await self.client.get_tags()
        self.assertIsInstance(r, list)
        for i in r:
            self.assertIsInstance(i, str)

    async def test_get_post_info(self):
        r = await kartra_api.KartraPost.fetch_post_info(1191)
        __import__("pprint").pprint(r.__dict__)
        self.assertIsInstance(r, kartra_api.KartraPost)