from config import Config


def test_config():
    config = Config()
    assert config['some_section'] == dict()
    config['some_section']['key'] = 'value'
    assert config.config['some_section']['key'] == 'value'
