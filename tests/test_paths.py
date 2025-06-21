import unittest
from unittest.mock import patch, MagicMock

import os
import sys

# Fake customtkinter to avoid dependency on GUI library during tests
class Dummy:
    def __init__(self, *a, **k):
        pass
    def __getattr__(self, name):
        return Dummy

dummy_module = MagicMock()
dummy_module.CTk = Dummy
dummy_module.CTkFrame = Dummy
dummy_module.CTkButton = Dummy
dummy_module.CTkLabel = Dummy
dummy_module.CTkProgressBar = Dummy
dummy_module.CTkTextbox = Dummy
dummy_module.CTkFont = Dummy
dummy_module.StringVar = Dummy
dummy_module.DoubleVar = Dummy
dummy_module.set_appearance_mode = lambda *a, **k: None
sys.modules.setdefault('customtkinter', dummy_module)
sys.modules.setdefault('requests', MagicMock())
sys.modules.setdefault('tqdm', MagicMock())

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import cdda_launcher

class BaseLauncher(cdda_launcher.CDDALauncher):
    def _create_ui(self):
        # Avoid creating GUI during tests
        pass

    def check_versions(self):
        # Skip network access
        pass

class PathTests(unittest.TestCase):
    def setUp(self):
        with patch.object(cdda_launcher, 'SingleInstance', new=MagicMock()):
            self.launcher = BaseLauncher()
        # use deterministic paths
        self.launcher.experimental_path = '/tmp/exp'
        self.launcher.stable_path = '/tmp/stable'
        self.launcher.bn_path = '/tmp/bn'

    def test_get_game_path(self):
        self.assertEqual(self.launcher.get_game_path('experimental'), '/tmp/exp')
        self.assertEqual(self.launcher.get_game_path('stable'), '/tmp/stable')
        self.assertEqual(self.launcher.get_game_path('bn'), '/tmp/bn')

    @patch('subprocess.Popen')
    def test_open_folder_bn(self, popen):
        self.launcher.open_folder('bn')
        popen.assert_called_once_with(['open', '/tmp/bn'])

    @patch('subprocess.Popen')
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_launch_game_bn(self, exists, listdir, popen):
        exists.return_value = True
        listdir.return_value = ['Cataclysm.app']
        self.launcher.launch_game('bn')
        popen.assert_called_once_with(['open', '/tmp/bn/Cataclysm.app'])

if __name__ == '__main__':
    unittest.main()
