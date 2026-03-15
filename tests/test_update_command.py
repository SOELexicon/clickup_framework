import os
import tempfile
import unittest
from unittest.mock import patch

from clickup_framework.commands.update_command import get_python_from_script


class TestUpdateCommandPythonResolution(unittest.TestCase):
    def test_windows_uses_companion_script_shebang(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            scripts_dir = os.path.join(temp_dir, "Scripts")
            os.makedirs(scripts_dir, exist_ok=True)

            cum_exe = os.path.join(scripts_dir, "cum.exe")
            companion = os.path.join(scripts_dir, "cum-script.py")

            with open(cum_exe, "wb") as f:
                f.write(b"")

            with open(companion, "w", encoding="utf-8") as f:
                f.write("#!C:\\\\Python311\\\\python.exe\n")
                f.write("print('stub')\n")

            with patch("clickup_framework.commands.update_command.platform.system", return_value="Windows"):
                with patch("clickup_framework.commands.update_command.get_current_cum_script_path", return_value=None):
                    python_path = get_python_from_script(cum_exe)

            self.assertEqual(python_path, r"C:\\Python311\\python.exe")

    def test_windows_prefers_current_interpreter_for_current_launcher(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            scripts_dir = os.path.join(temp_dir, "Scripts")
            os.makedirs(scripts_dir, exist_ok=True)

            cum_exe = os.path.join(scripts_dir, "cum.exe")
            current_python = os.path.join(temp_dir, "python.exe")

            with open(cum_exe, "wb") as f:
                f.write(b"")

            with open(current_python, "wb") as f:
                f.write(b"")

            with patch("clickup_framework.commands.update_command.platform.system", return_value="Windows"):
                with patch("clickup_framework.commands.update_command.get_current_cum_script_path", return_value=cum_exe):
                    with patch("clickup_framework.commands.update_command.sys.executable", current_python):
                        python_path = get_python_from_script(cum_exe)

            self.assertEqual(python_path, current_python)


if __name__ == "__main__":
    unittest.main()
