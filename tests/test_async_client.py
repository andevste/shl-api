"""Unit tests for AsyncSHLClient."""

import asyncio
from unittest.mock import MagicMock

from shl.async_client import AsyncSHLClient


def test_async_client_context_manager():
    async def run():
        async with AsyncSHLClient() as client:
            assert client._sync_client.base_url == "https://www.shl.se/api"

    asyncio.run(run())


def test_async_client_sync_wrapper():
    async def run():
        async with AsyncSHLClient() as client:
            client._sync_client.get_teams = MagicMock(return_value=[])
            teams = await client.get_teams()
            assert teams == []

    asyncio.run(run())
