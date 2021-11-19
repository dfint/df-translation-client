import pytest

from df_translation_client.app import App


@pytest.mark.timeout(1000)
def test_app():
    app = App(ignore_config_file=True, debug=True)
    app.main_window.after(100, app.main_window.quit)
    app.run()
