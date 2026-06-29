import unittest

from app.core.mt5_detection import (
    APPDATA_PLACEHOLDER,
    FILE_URI_PLACEHOLDER,
    LOCAL_APPDATA_PLACEHOLDER,
    NETWORK_PATH_PLACEHOLDER,
    USER_HOME_PLACEHOLDER,
    is_private_path_text,
    redact_public_path,
)


class PathRedactionTests(unittest.TestCase):
    def test_redacts_user_home_windows_paths(self) -> None:
        self.assertTrue(
            redact_public_path(r"C:\Users\Ricardo\AppData\Local\MetaQuotes").startswith(LOCAL_APPDATA_PLACEHOLDER)
        )
        self.assertTrue(redact_public_path("C:/Users/Ricardo/Documents/MT5").startswith(USER_HOME_PLACEHOLDER))

    def test_redacts_network_and_file_uri_paths(self) -> None:
        self.assertEqual(redact_public_path(r"\\server\share\terminal64.exe"), NETWORK_PATH_PLACEHOLDER)
        self.assertEqual(redact_public_path("file:///C:/Users/Ricardo/AppData/Local/file.txt"), FILE_URI_PLACEHOLDER)

    def test_redacts_environment_placeholders(self) -> None:
        self.assertTrue(redact_public_path(r"%USERPROFILE%\AppData\Local").startswith(USER_HOME_PLACEHOLDER))
        self.assertTrue(redact_public_path(r"%LOCALAPPDATA%\Programs").startswith(LOCAL_APPDATA_PLACEHOLDER))
        self.assertTrue(redact_public_path(r"%APPDATA%\MetaQuotes").startswith(APPDATA_PLACEHOLDER))

    def test_private_path_text_detection(self) -> None:
        for value in [
            r"C:\Users\Ricardo\AppData\Local",
            "C:/Users/Ricardo/Documents/MT5",
            r"\\server\share\file.json",
            "file:///C:/Users/Ricardo/file.json",
            "%USERPROFILE%\\Desktop",
        ]:
            self.assertTrue(is_private_path_text(value), value)


if __name__ == "__main__":
    unittest.main()
