"""Slidemaker API module.

このモジュールはSlidemakerのRESTful APIを提供します。

Main Application:
    app: FastAPIアプリケーションインスタンス

Usage:
    # Development server
    $ uvicorn slidemaker.api:app --reload

    # Production (AWS Lambda)
    from mangum import Mangum
    from slidemaker.api import app
    handler = Mangum(app)
"""

from slidemaker.api.main import app

__all__ = ["app"]
