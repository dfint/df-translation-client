import asyncio

import pytest

from df_translation_client.app import App


@pytest.mark.timeout(1)
def test_app():
    app = App(ignore_config_file=True, debug=True)

    async def close_after_100ms():
        await asyncio.sleep(0.1)
        app.main_window.quit()

    asyncio.get_event_loop().create_task(close_after_100ms())
    app.run()
