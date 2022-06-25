from df_translation_client.utils.config import Config


def test_config():
    config = Config()
    assert dict(config.init_section("some_section")) == dict()
    config._sections["some_section"]["key"] = "value"
    assert config._sections["some_section"]["key"] == "value"
