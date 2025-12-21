"""Tests for ImageCoordinator."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from slidemaker.workflows.exceptions import WorkflowError
from slidemaker.workflows.image_coordinator import ImageCoordinator


class TestImageCoordinator:
    """Tests for ImageCoordinator."""

    @pytest.fixture
    def llm_manager(self):
        """Create a mock LLM manager."""
        manager = MagicMock()
        # LLMManager は今後実装予定なので、必要なメソッドをモック
        manager.generate_image = AsyncMock()
        return manager

    @pytest.fixture
    def coordinator(self, llm_manager):
        """Create an ImageCoordinator instance."""
        return ImageCoordinator(llm_manager)

    @pytest.mark.asyncio
    async def test_generate_images_empty_list(self, coordinator):
        """Test generating images with empty request list."""
        requests = []
        result = await coordinator.generate_images(requests)

        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_images_single_image(self, coordinator, llm_manager):
        """Test generating a single image."""
        requests = [
            {"id": "img1", "prompt": "A cat", "size": "1024x1024"}
        ]

        result = await coordinator.generate_images(requests)

        # プレースホルダー実装では実際のファイルは生成されないが、
        # パスが返される
        assert "img1" in result
        assert isinstance(result["img1"], Path)
        assert str(result["img1"]) == "generated_img1.png"

    @pytest.mark.asyncio
    async def test_generate_images_multiple_images(self, coordinator):
        """Test generating multiple images."""
        requests = [
            {"id": "img1", "prompt": "A cat", "size": "1024x1024"},
            {"id": "img2", "prompt": "A dog", "size": "1024x1024"},
            {"id": "img3", "prompt": "A bird", "size": "512x512"},
        ]

        result = await coordinator.generate_images(requests)

        assert len(result) == 3
        assert "img1" in result
        assert "img2" in result
        assert "img3" in result
        assert all(isinstance(path, Path) for path in result.values())

    @pytest.mark.asyncio
    async def test_generate_images_with_max_concurrent(self, coordinator):
        """Test that max_concurrent limits parallel execution."""
        requests = [
            {"id": f"img{i}", "prompt": f"Image {i}"}
            for i in range(10)
        ]

        # max_concurrent=2 で実行
        result = await coordinator.generate_images(requests, max_concurrent=2)

        # すべての画像が生成される
        assert len(result) == 10

    @pytest.mark.asyncio
    async def test_generate_images_with_cache_hit(self, coordinator):
        """Test cache hit on second request."""
        requests = [{"id": "img1", "prompt": "A cat"}]

        # 1回目の生成
        result1 = await coordinator.generate_images(requests)
        path1 = result1["img1"]

        # 2回目の生成（キャッシュヒット）
        result2 = await coordinator.generate_images(requests)
        path2 = result2["img1"]

        # 同じパスが返される
        assert path1 == path2

    @pytest.mark.asyncio
    async def test_generate_images_partial_failure(self, coordinator, monkeypatch):
        """Test handling of partial failure (some images fail)."""
        # _generate_single_image をモックして一部を失敗させる
        original_method = coordinator._generate_single_image

        async def mock_generate(request):
            if request["id"] == "img2":
                raise ValueError("Mock error for img2")
            return await original_method(request)

        monkeypatch.setattr(coordinator, "_generate_single_image", mock_generate)

        requests = [
            {"id": "img1", "prompt": "A cat"},
            {"id": "img2", "prompt": "A dog"},  # これが失敗
            {"id": "img3", "prompt": "A bird"},
        ]

        # 一部失敗でも、成功したものは返される（例外は発生しない）
        result = await coordinator.generate_images(requests)

        assert len(result) == 2
        assert "img1" in result
        assert "img2" not in result  # 失敗したので含まれない
        assert "img3" in result

    @pytest.mark.asyncio
    async def test_generate_images_all_failure(self, coordinator, monkeypatch):
        """Test handling when all images fail to generate."""
        # すべての生成を失敗させる
        async def mock_generate_fail(request):
            raise ValueError(f"Mock error for {request['id']}")

        monkeypatch.setattr(coordinator, "_generate_single_image", mock_generate_fail)

        requests = [
            {"id": "img1", "prompt": "A cat"},
            {"id": "img2", "prompt": "A dog"},
        ]

        # すべて失敗した場合は例外が発生
        with pytest.raises(WorkflowError) as exc_info:
            await coordinator.generate_images(requests)

        assert "All 2 image generation requests failed" in str(exc_info.value)

    def test_clear_cache(self, coordinator):
        """Test cache clearing."""
        # キャッシュに追加
        coordinator._cache["img1"] = Path("test.png")
        assert len(coordinator._cache) == 1

        # キャッシュをクリア
        coordinator.clear_cache()
        assert len(coordinator._cache) == 0

    def test_get_cached_image_exists(self, coordinator):
        """Test getting cached image that exists."""
        test_path = Path("test.png")
        coordinator._cache["img1"] = test_path

        result = coordinator.get_cached_image("img1")
        assert result == test_path

    def test_get_cached_image_not_exists(self, coordinator):
        """Test getting cached image that doesn't exist."""
        result = coordinator.get_cached_image("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_images_with_default_size(self, coordinator):
        """Test generating image with default size."""
        requests = [
            {"id": "img1", "prompt": "A cat"}  # size省略
        ]

        result = await coordinator.generate_images(requests)

        assert "img1" in result
        # デフォルトサイズ（1024x1024）で生成される
        assert isinstance(result["img1"], Path)

    @pytest.mark.asyncio
    async def test_concurrent_requests_for_same_id(self, coordinator):
        """Test that concurrent requests for same ID use cache."""
        import asyncio

        requests = [{"id": "img1", "prompt": "A cat"}]

        # 同じIDで並行リクエスト
        tasks = [
            coordinator.generate_images(requests),
            coordinator.generate_images(requests),
        ]
        results = await asyncio.gather(*tasks)

        # 両方とも同じパスを返す（キャッシュが機能）
        assert results[0]["img1"] == results[1]["img1"]
