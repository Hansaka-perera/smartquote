import os, tempfile
_tmp = tempfile.mkdtemp()
os.environ["SMARTQUOTE_DATA"] = _tmp
os.environ.pop("DATABASE_URL", None)
