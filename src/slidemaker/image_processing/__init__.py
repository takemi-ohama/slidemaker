"""Image Processing Module

画像処理機能を提供するモジュールです。

このモジュールは以下の機能を提供します:
- PDF/画像ファイルの読み込みと正規化
- LLMによる画像分析とスライド要素の検出
- 画像の切り出し
- 画像の保存
- 画像のクリーニング（ノイズ除去、コントラスト調整）

Modules:
    loader: PDF/画像ファイルの読み込み機能
    analyzer: LLM画像分析機能
    processor: 画像要素の処理機能
    exceptions: 画像処理固有の例外クラス
"""

from slidemaker.image_processing.analyzer import ImageAnalyzer
from slidemaker.image_processing.exceptions import (
    ImageAnalysisError,
    ImageCropError,
    ImageProcessingError,
    ImageSaveError,
)
from slidemaker.image_processing.loader import ImageLoader, ImageLoadError
from slidemaker.image_processing.processor import ImageProcessor

__all__ = [
    "ImageLoader",
    "ImageAnalyzer",
    "ImageProcessor",
    "ImageProcessingError",
    "ImageLoadError",
    "ImageAnalysisError",
    "ImageCropError",
    "ImageSaveError",
]
