from df_translation_client.app import App


def test_app():
    app = App(ignore_config_file=True, debug=True)
    app.main_window.update()
