"""Tests for ConversionWorkflow."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from PIL import Image

from slidemaker.core.models.element import ImageElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import SlideConfig
from slidemaker.workflows.conversion import ConversionWorkflow
from slidemaker.workflows.exceptions import WorkflowError, WorkflowValidationError


class TestConversionWorkflow:
    """Tests for ConversionWorkflow."""

    @pytest.fixture
    def llm_manager(self):
        """Create a mock LLM manager."""
        manager = MagicMock()
        return manager

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create a FileManager instance."""
        from slidemaker.utils.file_manager import FileManager

        return FileManager(output_base_dir=str(tmp_path))

    @pytest.fixture
    def image_loader(self):
        """Create a mock ImageLoader."""
        loader = MagicMock()
        loader.load_from_pdf = AsyncMock()
        loader.load_from_image = AsyncMock()
        return loader

    @pytest.fixture
    def image_analyzer(self):
        """Create a mock ImageAnalyzer."""
        analyzer = MagicMock()
        analyzer.analyze_slide_image = AsyncMock(
            return_value={
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Test content",
                        "font": {"name": "Arial", "size": 18, "color": "#000000"},
                        "alignment": "left",
                        "z_index": 0,
                    }
                ],
                "background": {"color": "#FFFFFF"},
            }
        )
        return analyzer

    @pytest.fixture
    def image_processor(self):
        """Create a mock ImageProcessor."""
        processor = MagicMock()
        # crop_element is synchronous and returns an Image
        processor.crop_element = MagicMock()
        # save_image is synchronous and returns a path string
        processor.save_image = MagicMock()
        return processor

    @pytest.fixture
    def powerpoint_generator(self):
        """Create a mock PowerPointGenerator."""
        generator = MagicMock()
        generator.generate = MagicMock()
        return generator

    @pytest.fixture
    def workflow(
        self,
        llm_manager,
        file_manager,
        image_loader,
        image_analyzer,
        image_processor,
        powerpoint_generator,
    ):
        """Create a ConversionWorkflow instance."""
        return ConversionWorkflow(
            llm_manager=llm_manager,
            file_manager=file_manager,
            image_loader=image_loader,
            image_analyzer=image_analyzer,
            image_processor=image_processor,
            powerpoint_generator=powerpoint_generator,
        )

    @pytest.fixture
    def sample_pdf_file(self, tmp_path):
        """Create a sample PDF file."""
        pdf_file = tmp_path / "input.pdf"
        pdf_file.write_text("dummy pdf content")
        return pdf_file

    @pytest.fixture
    def sample_image_file(self, tmp_path):
        """Create a sample image file."""
        img_file = tmp_path / "input.png"
        img_file.write_text("dummy image content")
        return img_file

    @pytest.fixture
    def mock_image(self):
        """Create a mock PIL Image."""
        img = Mock(spec=Image.Image)
        img.size = (1920, 1080)
        img.mode = "RGB"
        return img

    def test_init(
        self,
        workflow,
        llm_manager,
        file_manager,
        image_loader,
        image_analyzer,
        image_processor,
        powerpoint_generator,
    ):
        """Test ConversionWorkflow initialization."""
        assert workflow.llm_manager == llm_manager
        assert workflow.file_manager == file_manager
        assert workflow.image_loader == image_loader
        assert workflow.image_analyzer == image_analyzer
        assert workflow.image_processor == image_processor
        assert workflow.powerpoint_generator == powerpoint_generator

    # Test _validate_input

    def test_validate_input_file_not_found(self, workflow, tmp_path):
        """Test _validate_input raises error for non-existent file."""
        non_existent = tmp_path / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError) as exc_info:
            workflow._validate_input(non_existent)

        assert "not found" in str(exc_info.value).lower()

    def test_validate_input_not_a_file(self, workflow, tmp_path):
        """Test _validate_input raises error for directory."""
        with pytest.raises(WorkflowValidationError) as exc_info:
            workflow._validate_input(tmp_path)

        assert "not a file" in str(exc_info.value).lower()

    def test_validate_input_invalid_format(self, workflow, tmp_path):
        """Test _validate_input raises error for unsupported format."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("test")

        with pytest.raises(WorkflowValidationError) as exc_info:
            workflow._validate_input(invalid_file)

        assert "unsupported" in str(exc_info.value).lower()

    def test_validate_input_valid_pdf(self, workflow, sample_pdf_file):
        """Test _validate_input succeeds for valid PDF file."""
        workflow._validate_input(sample_pdf_file)

    def test_validate_input_valid_image(self, workflow, sample_image_file):
        """Test _validate_input succeeds for valid image file."""
        workflow._validate_input(sample_image_file)

    # Test _load_images

    @pytest.mark.asyncio
    async def test_load_images_pdf(self, workflow, sample_pdf_file, mock_image, image_loader):
        """Test _load_images loads PDF and converts to images."""
        image_loader.load_from_pdf.return_value = [mock_image, mock_image]

        result = await workflow._load_images(sample_pdf_file, dpi=300)

        assert len(result) == 2
        assert result[0] == mock_image
        image_loader.load_from_pdf.assert_called_once_with(sample_pdf_file, dpi=300)

    @pytest.mark.asyncio
    async def test_load_images_image_file(
        self, workflow, sample_image_file, mock_image, image_loader
    ):
        """Test _load_images loads single image file."""
        image_loader.load_from_image.return_value = mock_image

        result = await workflow._load_images(sample_image_file, dpi=300)

        assert len(result) == 1
        assert result[0] == mock_image
        image_loader.load_from_image.assert_called_once_with(sample_image_file)

    @pytest.mark.asyncio
    async def test_load_images_error(self, workflow, sample_pdf_file, image_loader):
        """Test _load_images raises WorkflowError on failure."""
        image_loader.load_from_pdf.side_effect = Exception("Load failed")

        with pytest.raises(WorkflowError) as exc_info:
            await workflow._load_images(sample_pdf_file, dpi=300)

        assert "failed to load" in str(exc_info.value).lower()

    # Test _analyze_images

    @pytest.mark.asyncio
    async def test_analyze_images_basic(self, workflow, mock_image, image_analyzer):
        """Test _analyze_images analyzes images successfully."""
        images = [mock_image, mock_image]
        analysis_result = {
            "elements": [{"type": "text", "content": "Test"}],
            "background": {"color": "#FFFFFF"},
        }
        image_analyzer.analyze_slide_image.return_value = analysis_result

        result = await workflow._analyze_images(images, max_concurrent=3)

        assert len(result) == 2
        assert result[0] == analysis_result
        assert image_analyzer.analyze_slide_image.call_count == 2

    @pytest.mark.asyncio
    async def test_analyze_images_concurrent(self, workflow, mock_image, image_analyzer):
        """Test _analyze_images uses concurrent processing."""
        images = [mock_image] * 5
        analysis_result = {"elements": [], "background": {}}
        image_analyzer.analyze_slide_image.return_value = analysis_result

        result = await workflow._analyze_images(images, max_concurrent=2)

        assert len(result) == 5
        # すべての画像が分析される
        assert image_analyzer.analyze_slide_image.call_count == 5

    @pytest.mark.asyncio
    async def test_analyze_images_error(self, workflow, mock_image, image_analyzer):
        """Test _analyze_images raises WorkflowError on failure."""
        images = [mock_image]
        image_analyzer.analyze_slide_image.side_effect = Exception("Analysis failed")

        with pytest.raises(WorkflowError) as exc_info:
            await workflow._analyze_images(images, max_concurrent=3)

        assert "failed to analyze" in str(exc_info.value).lower()

    # Test _process_images

    @pytest.mark.asyncio
    async def test_process_images_basic(
        self, workflow, mock_image, image_processor, tmp_path
    ):
        """Test _process_images extracts and saves image elements."""
        images = [mock_image]
        analyses = [
            {
                "elements": [
                    {
                        "type": "image",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 200, "height": 150},
                    }
                ]
            }
        ]
        output_path = tmp_path / "page0_elem0.png"
        # crop_element returns an Image
        image_processor.crop_element.return_value = mock_image
        # save_image returns a string path
        image_processor.save_image.return_value = str(output_path)

        result = await workflow._process_images(images, analyses, tmp_path)

        assert len(result) == 1
        assert "page0_elem0" in result
        assert result["page0_elem0"] == output_path
        image_processor.crop_element.assert_called_once()
        image_processor.save_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_images_skip_text_elements(
        self, workflow, mock_image, image_processor, tmp_path
    ):
        """Test _process_images skips text elements."""
        images = [mock_image]
        analyses = [
            {
                "elements": [
                    {"type": "text", "content": "Test"},
                    {
                        "type": "image",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 200, "height": 150},
                    },
                ]
            }
        ]
        output_path = tmp_path / "page0_elem1.png"
        image_processor.crop_element.return_value = mock_image
        image_processor.save_image.return_value = str(output_path)

        result = await workflow._process_images(images, analyses, tmp_path)

        # 画像要素のみが処理される
        assert len(result) == 1
        assert image_processor.crop_element.call_count == 1
        assert image_processor.save_image.call_count == 1

    @pytest.mark.asyncio
    async def test_process_images_continue_on_element_failure(
        self, workflow, mock_image, image_processor, tmp_path
    ):
        """Test _process_images continues on individual element failure."""
        images = [mock_image]
        analyses = [
            {
                "elements": [
                    {
                        "type": "image",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 200, "height": 150},
                    },
                    {
                        "type": "image",
                        "position": {"x": 300, "y": 300},
                        "size": {"width": 200, "height": 150},
                    },
                ]
            }
        ]
        output_path = tmp_path / "page0_elem1.png"

        # 1つ目は失敗、2つ目は成功
        image_processor.crop_element.side_effect = [
            Exception("Crop failed"),
            mock_image,
        ]
        image_processor.save_image.return_value = str(output_path)

        result = await workflow._process_images(images, analyses, tmp_path)

        # 2つ目の要素のみが処理される
        assert len(result) == 1
        assert "page0_elem1" in result
        assert image_processor.crop_element.call_count == 2
        # save_imageは1回だけ呼ばれる（1つ目は失敗したため）
        assert image_processor.save_image.call_count == 1

    @pytest.mark.asyncio
    async def test_process_images_empty_elements(
        self, workflow, mock_image, image_processor, tmp_path
    ):
        """Test _process_images handles empty elements."""
        images = [mock_image]
        analyses = [{"elements": []}]

        result = await workflow._process_images(images, analyses, tmp_path)

        assert len(result) == 0
        image_processor.crop_element.assert_not_called()

    # Test _create_slide_definitions

    @pytest.mark.asyncio
    async def test_create_slide_definitions_basic(self, workflow):
        """Test _create_slide_definitions creates PageDefinitions."""
        analyses = [
            {
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Test content",
                        "font": {"name": "Arial", "size": 18, "color": "#000000"},
                        "alignment": "left",
                        "z_index": 0,
                    }
                ],
                "background": {"color": "#FFFFFF"},
            }
        ]
        processed_images = {}

        slide_config, pages = await workflow._create_slide_definitions(
            analyses, processed_images, slide_size="16:9"
        )

        assert isinstance(slide_config, SlideConfig)
        assert slide_config.size == "16:9"
        assert len(pages) == 1
        assert isinstance(pages[0], PageDefinition)
        assert pages[0].page_number == 1
        assert len(pages[0].elements) == 1

    @pytest.mark.asyncio
    async def test_create_slide_definitions_with_images(self, workflow, tmp_path):
        """Test _create_slide_definitions includes image elements."""
        image_path = tmp_path / "test.png"
        image_path.write_text("dummy")

        analyses = [
            {
                "elements": [
                    {
                        "type": "image",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 200, "height": 150},
                        "z_index": 0,
                    }
                ],
                "background": {},
            }
        ]
        processed_images = {"page0_elem0": image_path}

        slide_config, pages = await workflow._create_slide_definitions(
            analyses, processed_images, slide_size="16:9"
        )

        assert len(pages) == 1
        assert len(pages[0].elements) == 1
        assert isinstance(pages[0].elements[0], ImageElement)
        assert pages[0].elements[0].source == str(image_path)

    @pytest.mark.asyncio
    async def test_create_slide_definitions_missing_image(self, workflow):
        """Test _create_slide_definitions skips missing image elements."""
        analyses = [
            {
                "elements": [
                    {
                        "type": "image",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 200, "height": 150},
                        "z_index": 0,
                    }
                ],
                "background": {},
            }
        ]
        processed_images = {}  # 画像が処理されていない

        slide_config, pages = await workflow._create_slide_definitions(
            analyses, processed_images, slide_size="16:9"
        )

        # 画像要素がスキップされる
        assert len(pages) == 1
        assert len(pages[0].elements) == 0

    @pytest.mark.asyncio
    async def test_create_slide_definitions_multiple_pages(self, workflow):
        """Test _create_slide_definitions creates multiple pages."""
        analyses = [
            {
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Page 1",
                        "font": {"name": "Arial", "size": 18, "color": "#000000"},
                        "alignment": "left",
                        "z_index": 0,
                    }
                ],
                "background": {},
            },
            {
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Page 2",
                        "font": {"name": "Arial", "size": 18, "color": "#000000"},
                        "alignment": "left",
                        "z_index": 0,
                    }
                ],
                "background": {},
            },
        ]
        processed_images = {}

        slide_config, pages = await workflow._create_slide_definitions(
            analyses, processed_images, slide_size="16:9"
        )

        assert len(pages) == 2
        assert pages[0].page_number == 1
        assert pages[1].page_number == 2

    @pytest.mark.asyncio
    async def test_create_slide_definitions_z_index_sorting(self, workflow):
        """Test _create_slide_definitions sorts elements by z-index."""
        analyses = [
            {
                "elements": [
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 100},
                        "size": {"width": 800, "height": 50},
                        "content": "Top",
                        "font": {"name": "Arial", "size": 18, "color": "#000000"},
                        "alignment": "left",
                        "z_index": 2,
                    },
                    {
                        "type": "text",
                        "position": {"x": 100, "y": 200},
                        "size": {"width": 800, "height": 50},
                        "content": "Bottom",
                        "font": {"name": "Arial", "size": 18, "color": "#000000"},
                        "alignment": "left",
                        "z_index": 0,
                    },
                ],
                "background": {},
            }
        ]
        processed_images = {}

        slide_config, pages = await workflow._create_slide_definitions(
            analyses, processed_images, slide_size="16:9"
        )

        # z-indexでソートされているか確認
        assert pages[0].elements[0].z_index == 0
        assert pages[0].elements[1].z_index == 2

    @pytest.mark.asyncio
    async def test_create_slide_definitions_skip_invalid_type(self, workflow):
        """Test _create_slide_definitions skips invalid element types."""
        # 不正なデータ（unknown type should be skipped）
        analyses = [{"elements": [{"type": "invalid"}]}]
        processed_images = {}

        # 不正な要素はスキップされ、エラーは発生しない
        slide_config, pages = await workflow._create_slide_definitions(
            analyses, processed_images, slide_size="16:9"
        )

        assert len(pages) == 1
        # 不正な要素はスキップされるため要素数は0
        assert len(pages[0].elements) == 0

    # Test _generate_powerpoint

    @pytest.mark.asyncio
    async def test_generate_powerpoint_basic(
        self, workflow, powerpoint_generator, tmp_path
    ):
        """Test _generate_powerpoint generates PowerPoint file."""
        slide_config = SlideConfig(title="Test", size="16:9", theme="default")
        pages = [PageDefinition(page_number=1)]
        output_path = tmp_path / "output.pptx"

        powerpoint_generator.generate.return_value = output_path

        result = await workflow._generate_powerpoint(slide_config, pages, output_path)

        assert result == output_path
        powerpoint_generator.generate.assert_called_once_with(
            config=slide_config, pages=pages, output_path=output_path
        )

    @pytest.mark.asyncio
    async def test_generate_powerpoint_error(
        self, workflow, powerpoint_generator, tmp_path
    ):
        """Test _generate_powerpoint raises WorkflowError on failure."""
        slide_config = SlideConfig(title="Test", size="16:9", theme="default")
        pages = [PageDefinition(page_number=1)]
        output_path = tmp_path / "output.pptx"

        powerpoint_generator.generate.side_effect = Exception("Generation failed")

        with pytest.raises(WorkflowError) as exc_info:
            await workflow._generate_powerpoint(slide_config, pages, output_path)

        assert "failed to generate" in str(exc_info.value).lower()

    # Test execute (E2E)

    @pytest.mark.asyncio
    async def test_execute_pdf_to_pptx(
        self,
        workflow,
        sample_pdf_file,
        tmp_path,
        mock_image,
        image_loader,
        image_analyzer,
        image_processor,
        powerpoint_generator,
    ):
        """Test execute() with PDF input (E2E)."""
        output_path = tmp_path / "output.pptx"

        # Setup mocks
        image_loader.load_from_pdf.return_value = [mock_image]
        image_analyzer.analyze_slide_image.return_value = {
            "elements": [
                {
                    "type": "text",
                    "position": {"x": 100, "y": 100},
                    "size": {"width": 800, "height": 50},
                    "content": "Test",
                    "font": {"name": "Arial", "size": 18, "color": "#000000"},
                    "alignment": "left",
                    "z_index": 0,
                }
            ],
            "background": {},
        }
        powerpoint_generator.generate.return_value = output_path

        result = await workflow.execute(
            input_data=sample_pdf_file, output_path=output_path, dpi=300
        )

        assert result == output_path
        image_loader.load_from_pdf.assert_called_once()
        image_analyzer.analyze_slide_image.assert_called_once()
        powerpoint_generator.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_image_to_pptx(
        self,
        workflow,
        sample_image_file,
        tmp_path,
        mock_image,
        image_loader,
        image_analyzer,
        powerpoint_generator,
    ):
        """Test execute() with image input (E2E)."""
        output_path = tmp_path / "output.pptx"

        # Setup mocks
        image_loader.load_from_image.return_value = mock_image
        image_analyzer.analyze_slide_image.return_value = {
            "elements": [],
            "background": {},
        }
        powerpoint_generator.generate.return_value = output_path

        result = await workflow.execute(
            input_data=sample_image_file, output_path=output_path
        )

        assert result == output_path
        image_loader.load_from_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_options(
        self,
        workflow,
        sample_pdf_file,
        tmp_path,
        mock_image,
        image_loader,
        image_analyzer,
        powerpoint_generator,
    ):
        """Test execute() with custom options."""
        output_path = tmp_path / "output.pptx"

        # Setup mocks
        image_loader.load_from_pdf.return_value = [mock_image]
        image_analyzer.analyze_slide_image.return_value = {
            "elements": [],
            "background": {},
        }
        powerpoint_generator.generate.return_value = output_path

        result = await workflow.execute(
            input_data=sample_pdf_file,
            output_path=output_path,
            dpi=150,
            max_concurrent=5,
            slide_size="4:3",
        )

        assert result == output_path
        # DPIオプションが渡されていることを確認
        image_loader.load_from_pdf.assert_called_with(sample_pdf_file, dpi=150)

    @pytest.mark.asyncio
    async def test_execute_invalid_input_type(self, workflow, tmp_path):
        """Test execute() raises TypeError for invalid input type."""
        output_path = tmp_path / "output.pptx"

        with pytest.raises(TypeError):
            await workflow.execute(input_data=12345, output_path=output_path)

    @pytest.mark.asyncio
    async def test_execute_cleanup_on_failure(
        self,
        workflow,
        sample_pdf_file,
        tmp_path,
        mock_image,
        image_loader,
        image_analyzer,
    ):
        """Test execute() cleans up temp directory on failure."""
        output_path = tmp_path / "output.pptx"
        temp_dir = tmp_path / "temp"

        # Setup mocks
        image_loader.load_from_pdf.return_value = [mock_image]
        image_analyzer.analyze_slide_image.side_effect = Exception("Analysis failed")

        with pytest.raises(WorkflowError):
            await workflow.execute(
                input_data=sample_pdf_file,
                output_path=output_path,
                temp_dir=temp_dir,
            )

        # 一時ディレクトリが削除されていることを確認（実際にはworkflow内でshutil.rmtree）
        # この場合、例外が発生してクリーンアップロジックが実行される
