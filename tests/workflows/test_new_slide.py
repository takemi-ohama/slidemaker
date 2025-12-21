"""Tests for NewSlideWorkflow."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from slidemaker.core.models.common import Position, Size
from slidemaker.core.models.element import ImageElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import SlideConfig
from slidemaker.workflows.exceptions import WorkflowValidationError
from slidemaker.workflows.new_slide import NewSlideWorkflow


class TestNewSlideWorkflow:
    """Tests for NewSlideWorkflow."""

    @pytest.fixture
    def llm_manager(self):
        """Create a mock LLM manager."""
        manager = MagicMock()
        manager.generate_structured = AsyncMock(
            return_value={
                "slide_config": {"size": "16:9", "theme": "default"},
                "pages": [
                    {
                        "title": "Test Slide",
                        "elements": [
                            {
                                "type": "text",
                                "position": {"x": 100, "y": 100},
                                "size": {"width": 800, "height": 50},
                                "content": "Test content",
                            }
                        ],
                    }
                ],
            }
        )
        return manager

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create a FileManager instance."""
        from slidemaker.utils.file_manager import FileManager

        return FileManager(output_base_dir=str(tmp_path))

    @pytest.fixture
    def workflow(self, llm_manager, file_manager):
        """Create a NewSlideWorkflow instance."""
        return NewSlideWorkflow(llm_manager, file_manager)

    @pytest.fixture
    def sample_markdown_file(self, tmp_path):
        """Create a sample markdown file."""
        md_file = tmp_path / "input.md"
        md_file.write_text("# Test Presentation\n\nThis is a test.")
        return md_file

    def test_init(self, workflow, llm_manager, file_manager):
        """Test NewSlideWorkflow initialization."""
        assert workflow.llm_manager == llm_manager
        assert workflow.file_manager == file_manager
        assert workflow.composition_parser is not None
        assert workflow.image_coordinator is not None

    def test_validate_input_file_not_found(self, workflow, tmp_path):
        """Test _validate_input raises error for non-existent file."""
        non_existent = tmp_path / "nonexistent.md"

        with pytest.raises(WorkflowValidationError) as exc_info:
            workflow._validate_input(non_existent)

        assert "not found" in str(exc_info.value).lower()

    def test_validate_input_not_a_file(self, workflow, tmp_path):
        """Test _validate_input raises error for directory."""
        with pytest.raises(WorkflowValidationError) as exc_info:
            workflow._validate_input(tmp_path)

        assert "not a file" in str(exc_info.value).lower()

    def test_validate_input_valid_file(self, workflow, sample_markdown_file):
        """Test _validate_input succeeds for valid file."""
        # 有効なファイルの場合は例外が発生しない
        workflow._validate_input(sample_markdown_file)

    @pytest.mark.asyncio
    async def test_parse_markdown(self, workflow, sample_markdown_file):
        """Test _parse_markdown reads and parses markdown file."""
        result = await workflow._parse_markdown(sample_markdown_file)

        assert "content" in result
        assert "metadata" in result
        assert "# Test Presentation" in result["content"]
        assert result["metadata"]["source"] == str(sample_markdown_file)
        assert result["metadata"]["length"] > 0

    @pytest.mark.asyncio
    async def test_parse_markdown_file_not_found(self, workflow, tmp_path):
        """Test _parse_markdown raises error for non-existent file."""
        non_existent = tmp_path / "nonexistent.md"

        with pytest.raises(OSError):
            await workflow._parse_markdown(non_existent)

    def test_parse_composition(self, workflow):
        """Test _parse_composition converts composition to models."""
        composition = {
            "slide_config": {"size": "16:9", "theme": "corporate"},
            "pages": [
                {
                    "title": "Slide 1",
                    "background_color": "#FFFFFF",
                    "elements": [
                        {
                            "type": "text",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 800, "height": 50},
                            "content": "Test",
                        }
                    ],
                }
            ],
        }

        slide_config, pages = workflow._parse_composition(composition)

        assert isinstance(slide_config, SlideConfig)
        assert slide_config.size == "16:9"
        assert slide_config.theme == "corporate"

        assert len(pages) == 1
        assert isinstance(pages[0], PageDefinition)
        assert pages[0].title == "Slide 1"

    def test_extract_image_requests_no_images(self, workflow):
        """Test _extract_image_requests with no images."""
        composition = {
            "pages": [
                {
                    "title": "Text Only",
                    "elements": [
                        {
                            "type": "text",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 800, "height": 50},
                            "content": "Text",
                        }
                    ],
                }
            ]
        }

        requests = workflow._extract_image_requests(composition)
        assert requests == []

    def test_extract_image_requests_with_images(self, workflow):
        """Test _extract_image_requests extracts image generation requests."""
        composition = {
            "pages": [
                {
                    "title": "Image Slide",
                    "elements": [
                        {
                            "type": "image",
                            "id": "img1",
                            "prompt": "A cat",
                            "size": "1024x1024",
                            "generate": True,
                        },
                        {
                            "type": "image",
                            "id": "img2",
                            "prompt": "A dog",
                            "generate": True,
                        },
                        {
                            "type": "image",
                            "id": "img3",
                            "source": "existing.png",
                            "generate": False,  # 既存画像
                        },
                    ],
                }
            ]
        }

        requests = workflow._extract_image_requests(composition)

        assert len(requests) == 2  # generate=True のみ
        assert requests[0]["id"] == "img1"
        assert requests[0]["prompt"] == "A cat"
        assert requests[1]["id"] == "img2"

    def test_update_image_paths(self, workflow):
        """Test _update_image_paths updates PageDefinition with generated paths."""
        pages = [
            PageDefinition(
                page_number=1,
                title="Test",
                elements=[
                    ImageElement(
                        position=Position(x=100, y=100),
                        size=Size(width=400, height=300),
                        source="generated_img1",  # プレースホルダー
                    )
                ],
            )
        ]

        generated_images = {
            "img1": Path("/path/to/generated_img1.png"),
        }

        updated_pages = workflow._update_image_paths(pages, generated_images)

        assert len(updated_pages) == 1
        element = updated_pages[0].elements[0]
        assert isinstance(element, ImageElement)
        assert "/path/to/generated_img1.png" in element.source

    def test_update_image_paths_no_match(self, workflow):
        """Test _update_image_paths when no ID matches."""
        pages = [
            PageDefinition(
                page_number=1,
                title="Test",
                elements=[
                    ImageElement(
                        position=Position(x=100, y=100),
                        size=Size(width=400, height=300),
                        source="other_image.png",
                    )
                ],
            )
        ]

        generated_images = {
            "img1": Path("/path/to/generated_img1.png"),
        }

        updated_pages = workflow._update_image_paths(pages, generated_images)

        # マッチしないので元のままsource
        element = updated_pages[0].elements[0]
        assert element.source == "other_image.png"

    @pytest.mark.asyncio
    @patch("slidemaker.workflows.new_slide.PowerPointGenerator")
    async def test_execute_without_images(
        self,
        mock_pptx_gen,
        workflow,
        sample_markdown_file,
        tmp_path,
    ):
        """Test execute workflow without image generation."""
        output_path = tmp_path / "output.pptx"

        # PowerPointGenerator のモック
        mock_generator = MagicMock()
        mock_generator.generate.return_value = output_path
        mock_pptx_gen.return_value = mock_generator

        result = await workflow.execute(
            input_data=sample_markdown_file,
            output_path=output_path,
            theme="default",
            generate_images=False,
        )

        assert result == output_path
        mock_pptx_gen.assert_called_once()
        mock_generator.generate.assert_called_once()

    @pytest.mark.asyncio
    @patch("slidemaker.workflows.new_slide.PowerPointGenerator")
    async def test_execute_with_images(
        self,
        mock_pptx_gen,
        workflow,
        sample_markdown_file,
        tmp_path,
    ):
        """Test execute workflow with image generation."""
        output_path = tmp_path / "output.pptx"

        # PowerPointGenerator のモック
        mock_generator = MagicMock()
        mock_generator.generate.return_value = output_path
        mock_pptx_gen.return_value = mock_generator

        # LLM の composition にimage生成リクエストを含める
        workflow.llm_manager.generate_structured.return_value = {
            "slide_config": {"size": "16:9"},
            "pages": [
                {
                    "title": "Image Slide",
                    "elements": [
                        {
                            "type": "image",
                            "id": "img1",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 400, "height": 300},
                            "source": "generated_img1",
                            "prompt": "A test image",
                            "generate": True,
                        }
                    ],
                }
            ],
        }

        result = await workflow.execute(
            input_data=sample_markdown_file,
            output_path=output_path,
            generate_images=True,
        )

        assert result == output_path

    @pytest.mark.asyncio
    async def test_execute_with_invalid_input(self, workflow, tmp_path):
        """Test execute raises error for invalid input."""
        non_existent = tmp_path / "nonexistent.md"
        output_path = tmp_path / "output.pptx"

        with pytest.raises(WorkflowValidationError):
            await workflow.execute(
                input_data=non_existent,
                output_path=output_path,
            )

    @pytest.mark.asyncio
    async def test_execute_with_string_input_data(
        self,
        workflow,
        sample_markdown_file,
        tmp_path,
    ):
        """Test execute accepts string path as input_data."""
        output_path = tmp_path / "output.pptx"

        with patch("slidemaker.workflows.new_slide.PowerPointGenerator") as mock_gen:
            mock_generator = MagicMock()
            mock_generator.generate.return_value = output_path
            mock_gen.return_value = mock_generator

            # 文字列パスを渡す
            result = await workflow.execute(
                input_data=str(sample_markdown_file),
                output_path=output_path,
                generate_images=False,
            )

            assert result == output_path

    @pytest.mark.asyncio
    async def test_execute_with_custom_options(
        self,
        workflow,
        sample_markdown_file,
        tmp_path,
    ):
        """Test execute with custom options."""
        output_path = tmp_path / "output.pptx"

        with patch("slidemaker.workflows.new_slide.PowerPointGenerator") as mock_gen:
            mock_generator = MagicMock()
            mock_generator.generate.return_value = output_path
            mock_gen.return_value = mock_generator

            result = await workflow.execute(
                input_data=sample_markdown_file,
                output_path=output_path,
                theme="corporate",
                slide_size="4:3",
                max_retries=5,
            )

            assert result == output_path
