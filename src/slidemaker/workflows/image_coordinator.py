"""Image Generation Coordinator

画像生成リクエストの管理と並行実行を行います。

Main Components:
    - ImageCoordinator: 画像生成の調整と管理
"""

import asyncio
from pathlib import Path
from typing import Any

import structlog

from slidemaker.llm.manager import LLMManager
from slidemaker.workflows.exceptions import WorkflowError


class ImageCoordinator:
    """画像生成の調整と管理

    複数の画像生成リクエストを並行実行し、
    結果をキャッシュして効率的に処理します。
    セマフォを使用して同時実行数を制限し、
    システムリソースを適切に管理します。

    Attributes:
        llm_manager: LLMマネージャー
        logger: 構造化ロガー
        _cache: 生成結果のキャッシュ

    Example:
        >>> coordinator = ImageCoordinator(llm_manager)
        >>> requests = [
        ...     {"id": "img1", "prompt": "A cat", "size": "1024x1024"},
        ...     {"id": "img2", "prompt": "A dog", "size": "1024x1024"}
        ... ]
        >>> results = await coordinator.generate_images(requests)
    """

    def __init__(self, llm_manager: LLMManager) -> None:
        """ImageCoordinatorの初期化

        Args:
            llm_manager: LLMマネージャー
        """
        self.llm_manager = llm_manager
        self.logger = structlog.get_logger(__name__)
        self._cache: dict[str, Path] = {}

    async def generate_images(
        self,
        image_requests: list[dict[str, Any]],
        max_concurrent: int = 3,
    ) -> dict[str, Path]:
        """複数画像の生成

        複数の画像生成リクエストを並行実行します。
        max_concurrentパラメータで同時実行数を制限できます。

        Args:
            image_requests: 画像生成リクエストのリスト
                各リクエストは以下のフィールドを含む:
                - id (str): 画像ID
                - prompt (str): 生成プロンプト
                - size (str, optional): 画像サイズ（例: "1024x1024"）
            max_concurrent: 最大同時実行数（デフォルト: 3）

        Returns:
            dict: {image_id: generated_path} の辞書
                生成に失敗した画像はresultに含まれません

        Raises:
            WorkflowError: すべての画像生成が失敗した場合

        Example:
            >>> requests = [
            ...     {"id": "img1", "prompt": "A cat"},
            ...     {"id": "img2", "prompt": "A dog"}
            ... ]
            >>> results = await coordinator.generate_images(
            ...     requests,
            ...     max_concurrent=2
            ... )
            >>> print(results)
            {'img1': Path('generated_img1.png'), 'img2': Path('generated_img2.png')}
        """
        if not image_requests:
            self.logger.debug("no_image_requests")
            return {}

        self.logger.info(
            "image_generation_start",
            count=len(image_requests),
            max_concurrent=max_concurrent,
        )

        # セマフォで並行実行数を制限
        semaphore = asyncio.Semaphore(max_concurrent)

        tasks = [
            self._generate_with_semaphore(request, semaphore)
            for request in image_requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果の集約
        generated_images: dict[str, Path] = {}
        errors: list[tuple[str, Exception]] = []

        for request, result in zip(image_requests, results, strict=True):
            image_id = request["id"]

            if isinstance(result, Exception):
                errors.append((image_id, result))
                self.logger.error(
                    "image_generation_failed",
                    image_id=image_id,
                    error=str(result),
                    error_type=type(result).__name__,
                )
            elif isinstance(result, Path):
                generated_images[image_id] = result
                self.logger.debug(
                    "image_generated",
                    image_id=image_id,
                    path=str(result),
                )

        # エラーの処理
        if errors:
            if len(errors) == len(image_requests):
                # すべて失敗した場合はエラーを発生
                error_msg = f"All {len(errors)} image generation requests failed"
                self.logger.error("all_images_failed", errors=errors)
                raise WorkflowError(error_msg)
            else:
                # 一部失敗の場合は警告ログのみ（ワークフローは続行）
                self.logger.warning(
                    "image_generation_partial_failure",
                    failed_count=len(errors),
                    success_count=len(generated_images),
                )

        self.logger.info(
            "image_generation_complete",
            success=len(generated_images),
            failed=len(errors),
        )

        return generated_images

    async def _generate_with_semaphore(
        self,
        request: dict[str, Any],
        semaphore: asyncio.Semaphore,
    ) -> Path:
        """セマフォ付き画像生成

        セマフォを使用して並行実行数を制限しながら画像を生成します。

        Args:
            request: 画像生成リクエスト
            semaphore: 並行実行制御用セマフォ

        Returns:
            Path: 生成された画像のパス

        Raises:
            WorkflowError: 画像生成エラー
        """
        async with semaphore:
            return await self._generate_single_image(request)

    async def _generate_single_image(self, request: dict[str, Any]) -> Path:
        """単一画像の生成

        1つの画像を生成します。キャッシュがある場合はキャッシュを返します。

        Args:
            request: 画像生成リクエスト
                - id (str): 画像ID
                - prompt (str): 生成プロンプト
                - size (str, optional): 画像サイズ

        Returns:
            Path: 生成された画像のパス

        Raises:
            WorkflowError: 画像生成エラー

        Example:
            >>> request = {"id": "img1", "prompt": "A cat", "size": "1024x1024"}
            >>> path = await coordinator._generate_single_image(request)
        """
        image_id = request["id"]

        # キャッシュチェック
        if image_id in self._cache:
            self.logger.debug("image_cache_hit", image_id=image_id)
            return self._cache[image_id]

        # 画像生成パラメータ
        prompt = request["prompt"]
        size = request.get("size", "1024x1024")

        self.logger.debug(
            "generating_image",
            image_id=image_id,
            prompt=prompt,
            size=size,
        )

        try:
            # TODO: 実際の画像生成LLMアダプタを使用
            # 現在はプレースホルダー実装
            #
            # 将来的には以下のように実装:
            # image_data = await self.llm_manager.generate_image(
            #     adapter_name="image_generation",
            #     prompt=prompt,
            #     size=size,
            # )
            # image_path = self._save_generated_image(image_id, image_data)

            # プレースホルダー: 実際のファイルは生成されない
            image_path = Path(f"generated_{image_id}.png")

            # キャッシュに保存
            self._cache[image_id] = image_path

            self.logger.info(
                "image_generated_successfully",
                image_id=image_id,
                path=str(image_path),
            )

            return image_path

        except Exception as e:
            error_msg = f"Failed to generate image '{image_id}': {e}"
            self.logger.error(
                "image_generation_error",
                image_id=image_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise WorkflowError(error_msg) from e

    def clear_cache(self) -> None:
        """キャッシュのクリア

        生成結果のキャッシュをクリアします。

        Example:
            >>> coordinator.clear_cache()
        """
        self._cache.clear()
        self.logger.debug("cache_cleared")

    def get_cached_image(self, image_id: str) -> Path | None:
        """キャッシュから画像パスを取得

        Args:
            image_id: 画像ID

        Returns:
            Path | None: キャッシュされた画像のパス（存在しない場合はNone）

        Example:
            >>> path = coordinator.get_cached_image("img1")
        """
        return self._cache.get(image_id)
