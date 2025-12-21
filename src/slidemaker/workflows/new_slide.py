"""New Slide Workflow

Markdownファイルから新規PowerPointファイルを生成するワークフローです。

Main Components:
    - NewSlideWorkflow: Markdown → PowerPoint の完全パイプライン
"""

from pathlib import Path
from typing import Any

import structlog

from slidemaker.core.models.element import ImageElement
from slidemaker.core.models.page_definition import PageDefinition
from slidemaker.core.models.slide_config import SlideConfig
from slidemaker.llm.manager import LLMManager
from slidemaker.pptx.generator import PowerPointGenerator
from slidemaker.utils.file_manager import FileManager
from slidemaker.workflows.base import WorkflowOrchestrator
from slidemaker.workflows.composition_parser import CompositionParser
from slidemaker.workflows.exceptions import WorkflowValidationError
from slidemaker.workflows.image_coordinator import ImageCoordinator


class NewSlideWorkflow(WorkflowOrchestrator):
    """Markdownから新規スライド作成ワークフロー

    Markdownファイルを入力として、LLMによる構成生成、
    画像生成（オプション）、PowerPoint生成を実行します。

    Workflow Steps:
        1. Markdownパース
        2. LLMによる構成生成
        3. CompositionParserで構成解析
        4. 画像生成（必要に応じて）
        5. PowerPoint生成

    Attributes:
        composition_parser: 構成パーサー
        image_coordinator: 画像生成コーディネーター

    Example:
        >>> workflow = NewSlideWorkflow(llm_manager, file_manager)
        >>> result = await workflow.execute(
        ...     markdown_path=Path("input.md"),
        ...     output_path=Path("output.pptx"),
        ...     theme="corporate",
        ...     generate_images=False
        ... )
    """

    def __init__(
        self,
        llm_manager: LLMManager,
        file_manager: FileManager,
    ) -> None:
        """NewSlideWorkflowの初期化

        Args:
            llm_manager: LLMマネージャー
            file_manager: ファイルマネージャー
        """
        super().__init__(llm_manager, file_manager)
        self.composition_parser = CompositionParser()
        self.image_coordinator = ImageCoordinator(llm_manager)
        self.logger = structlog.get_logger(__name__)

    async def execute(
        self,
        input_data: Any,
        output_path: Path,
        **options: Any,
    ) -> Path:
        """ワークフローの実行

        Markdownファイルから最終的なPowerPointファイルまでの
        完全なパイプラインを実行します。

        Args:
            input_data: 入力Markdownファイルのパス（Path型を期待）
            output_path: 出力PowerPointファイルのパス
            **options: オプション
                - theme (str): テーマ名（デフォルト: "default"）
                - generate_images (bool): 画像生成を実行するか（デフォルト: False）
                - slide_size (str): スライドサイズ（デフォルト: "16:9"）
                - max_retries (int): ステップの最大リトライ回数（デフォルト: 3）

        Returns:
            Path: 生成されたPowerPointファイルのパス

        Raises:
            WorkflowError: ワークフロー実行エラー
            WorkflowValidationError: 入力データのバリデーションエラー
            FileNotFoundError: 入力ファイルが存在しない
            TypeError: input_dataがPath型でない場合

        Example:
            >>> result = await workflow.execute(
            ...     input_data=Path("presentation.md"),
            ...     output_path=Path("output/slides.pptx"),
            ...     theme="corporate",
            ...     generate_images=True,
            ...     slide_size="16:9"
            ... )
        """
        # 入力データをPathに変換・検証
        if not isinstance(input_data, Path):
            try:
                markdown_path = Path(input_data)
            except (TypeError, ValueError) as e:
                raise TypeError(f"input_data must be a Path or path-like string: {e}") from e
        else:
            markdown_path = input_data

        self.logger.info(
            "new_slide_workflow_start",
            markdown_path=str(markdown_path),
            output_path=str(output_path),
            options=options,
        )

        # 入力のバリデーション
        self._validate_input(markdown_path)
        self._validate_output_path(output_path)

        # リトライ回数の設定
        max_retries = options.get("max_retries", 3)

        # Step 1: Markdownパース
        parsed_data = await self._run_step(
            "parse_markdown",
            self._parse_markdown,
            markdown_path,
            max_retries=max_retries,
        )

        # Step 2: LLMによる構成生成
        composition = await self._run_step(
            "generate_composition",
            self._generate_composition,
            parsed_data,
            options,
            max_retries=max_retries,
        )

        # Step 3: 構成のパースとPageDefinition作成
        result = await self._run_step(
            "parse_composition",
            self._parse_composition,
            composition,
            max_retries=max_retries,
        )
        slide_config, pages = result

        # Step 4: 画像生成（オプション）
        if options.get("generate_images", False):
            generated_images: dict[str, Path] = await self._run_step(
                "generate_images",
                self._generate_images,  # type: ignore[arg-type]
                composition,
                max_retries=max_retries,
            )

            # 画像パスをPageDefinitionに反映
            pages = self._update_image_paths(pages, generated_images)
        else:
            self.logger.debug("skipping_image_generation")

        # Step 5: PowerPoint生成
        result_path: Path = await self._run_step(
            "generate_powerpoint",
            self._generate_powerpoint,
            slide_config,
            pages,
            output_path,
            max_retries=1,  # PowerPoint生成は通常リトライ不要
        )

        self.logger.info(
            "new_slide_workflow_success",
            output_path=str(result_path),
        )

        return result_path

    def _validate_input(self, markdown_path: Path) -> None:
        """入力Markdownファイルのバリデーション

        Args:
            markdown_path: Markdownファイルのパス

        Raises:
            WorkflowValidationError: バリデーションエラー
        """
        if not markdown_path.exists():
            error_msg = f"Markdown file not found: {markdown_path}"
            self.logger.error("markdown_file_not_found", path=str(markdown_path))
            raise WorkflowValidationError(error_msg)

        if not markdown_path.is_file():
            error_msg = f"Markdown path is not a file: {markdown_path}"
            self.logger.error("markdown_path_not_file", path=str(markdown_path))
            raise WorkflowValidationError(error_msg)

        if markdown_path.suffix.lower() not in [".md", ".markdown"]:
            self.logger.warning(
                "unexpected_file_extension",
                path=str(markdown_path),
                expected=[".md", ".markdown"],
            )

    async def _parse_markdown(self, markdown_path: Path) -> dict[str, Any]:
        """Markdownファイルのパース

        Markdownファイルを読み込み、構造化されたデータとして返します。
        現在はシンプルにテキスト全体を返しますが、将来的には
        見出し、段落、リストなどを構造化してパースすることができます。

        Args:
            markdown_path: Markdownファイルのパス

        Returns:
            dict: パースされたデータ
                - content (str): Markdownの内容
                - metadata (dict): メタデータ

        Raises:
            OSError: ファイル読み込みエラー
        """
        self.logger.debug("parsing_markdown", path=str(markdown_path))

        try:
            markdown_content = markdown_path.read_text(encoding="utf-8")
        except OSError as e:
            error_msg = f"Failed to read Markdown file: {e}"
            self.logger.error("markdown_read_error", path=str(markdown_path), error=str(e))
            raise OSError(error_msg) from e

        # TODO: 将来的にはMarkdownの構造化パース（見出し、段落、リストなど）を実装
        # 例: markdown-it-py, mistune などのライブラリを使用
        parsed_data = {
            "content": markdown_content,
            "metadata": {
                "source": str(markdown_path),
                "length": len(markdown_content),
            },
        }

        self.logger.info(
            "markdown_parsed",
            path=str(markdown_path),
            length=len(markdown_content),
        )

        return parsed_data

    async def _generate_composition(
        self,
        parsed_data: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """LLMによる構成生成

        パースされたMarkdownデータを元に、LLMがスライドの
        構成（レイアウト、テキスト配置、画像配置など）を生成します。

        Args:
            parsed_data: パースされたMarkdownデータ
            options: ワークフローオプション

        Returns:
            dict: LLMが生成した構成データ（JSON）
                - slide_config (dict): スライド設定
                - pages (list): ページ定義のリスト

        Raises:
            LLMError: LLM呼び出しエラー
        """
        self.logger.debug("generating_composition")

        # TODO: 実際のプロンプトテンプレートを使用
        # from slidemaker.llm.prompts.composition import CompositionPrompt
        # prompt_builder = CompositionPrompt()
        # prompt = prompt_builder.build(
        #     content=parsed_data["content"],
        #     theme=options.get("theme"),
        #     slide_size=options.get("slide_size", "16:9"),
        # )

        # プレースホルダー実装: シンプルなプロンプト
        prompt = f"""
Given the following Markdown content, generate a PowerPoint slide structure in JSON format.

Markdown content:
{parsed_data["content"]}

Theme: {options.get("theme", "default")}
Slide size: {options.get("slide_size", "16:9")}

Please return a JSON object with the following structure:
{{
    "slide_config": {{
        "size": "16:9",
        "theme": "default"
    }},
    "pages": [
        {{
            "title": "Slide Title",
            "background_color": "#FFFFFF",
            "elements": [
                {{
                    "type": "text",
                    "position": {{"x": 100, "y": 200}},
                    "size": {{"width": 800, "height": 100}},
                    "content": "Text content",
                    "font": {{
                        "family": "Arial",
                        "size": 24,
                        "color": "#000000",
                        "bold": false
                    }},
                    "alignment": "left",
                    "z_index": 1
                }}
            ]
        }}
    ]
}}
"""

        # LLMによる構造化出力の生成
        # TODO: Phase 3で generate_structured メソッドを実装する必要があります
        composition = await self.llm_manager.generate_structured(  # type: ignore[attr-defined]
            adapter_name="composition",
            prompt=prompt,
            output_schema={
                "type": "object",
                "properties": {
                    "slide_config": {"type": "object"},
                    "pages": {"type": "array"},
                },
                "required": ["slide_config", "pages"],
            },
        )

        self.logger.info(
            "composition_generated",
            page_count=len(composition.get("pages", [])),
        )

        # 型アサーション: LLMが正しい形式を返すことを想定
        return composition  # type: ignore[no-any-return]

    def _parse_composition(
        self,
        composition: dict[str, Any],
    ) -> tuple[SlideConfig, list[PageDefinition]]:
        """構成データのパースとPageDefinition作成

        LLMが生成した構成データをCompositionParserで解析し、
        SlideConfigとPageDefinitionのリストに変換します。

        Args:
            composition: LLMが生成した構成データ

        Returns:
            tuple: (SlideConfig, list[PageDefinition])

        Raises:
            WorkflowValidationError: パースエラー
        """
        self.logger.debug("parsing_composition")

        slide_config = self.composition_parser.parse_slide_config(
            composition.get("slide_config", {})
        )

        pages = self.composition_parser.parse_pages(composition.get("pages", []))

        self.logger.info(
            "composition_parsed",
            slide_size=slide_config.size,
            page_count=len(pages),
        )

        return slide_config, pages

    async def _generate_images(
        self,
        composition: dict[str, Any],
    ) -> dict[str, Path]:
        """画像生成

        構成データから画像生成リクエストを抽出し、
        ImageCoordinatorで並行生成します。

        Args:
            composition: 構成データ（画像生成リクエスト含む）

        Returns:
            dict: {image_id: generated_path}
        """
        self.logger.debug("extracting_image_requests")

        image_requests = self._extract_image_requests(composition)

        if not image_requests:
            self.logger.info("no_images_to_generate")
            return {}

        self.logger.info("generating_images", count=len(image_requests))

        generated_images = await self.image_coordinator.generate_images(image_requests)

        self.logger.info("images_generated", count=len(generated_images))

        return generated_images

    def _extract_image_requests(
        self,
        composition: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """構成データから画像生成リクエストを抽出

        構成データを走査し、"generate": true フラグが立っている
        画像要素を抽出して、画像生成リクエストのリストを作成します。

        Args:
            composition: 構成データ

        Returns:
            list: 画像生成リクエストのリスト
                各リクエストは以下のフィールドを含む:
                - id (str): 画像ID
                - prompt (str): 生成プロンプト
                - size (str): 画像サイズ
        """
        requests = []

        for page in composition.get("pages", []):
            for element in page.get("elements", []):
                if element.get("type") == "image" and element.get("generate"):
                    requests.append(
                        {
                            "id": element.get("id"),
                            "prompt": element.get("prompt"),
                            "size": element.get("size", "1024x1024"),
                        }
                    )

        self.logger.debug("image_requests_extracted", count=len(requests))

        return requests

    def _update_image_paths(
        self,
        pages: list[PageDefinition],
        generated_images: dict[str, Path],
    ) -> list[PageDefinition]:
        """PageDefinitionに生成された画像パスを反映

        画像生成が完了した後、PageDefinitionの画像要素の
        sourceフィールドを生成された画像のパスで更新します。

        Args:
            pages: PageDefinitionのリスト
            generated_images: {image_id: generated_path}

        Returns:
            list: 更新されたPageDefinitionのリスト
        """
        self.logger.debug("updating_image_paths", count=len(generated_images))

        updated_pages = []

        for page in pages:
            updated_elements = []

            for element in page.elements:
                if isinstance(element, ImageElement):
                    # 画像IDがsourceに含まれている場合は置き換え
                    # 例: source="generated_img1" → "generated_img1.png"
                    source = element.source
                    for image_id, generated_path in generated_images.items():
                        if image_id in source:
                            # 新しいImageElementを作成（Pydanticモデルはimmutable）
                            element = ImageElement(
                                position=element.position,
                                size=element.size,
                                source=str(generated_path),
                                fit_mode=element.fit_mode,
                                z_index=element.z_index,
                            )
                            self.logger.debug(
                                "image_path_updated",
                                image_id=image_id,
                                path=str(generated_path),
                            )
                            break

                updated_elements.append(element)

            # 新しいPageDefinitionを作成
            updated_page = PageDefinition(
                page_number=page.page_number,
                title=page.title,
                background_color=page.background_color,
                background_image=page.background_image,
                elements=updated_elements,
            )
            updated_pages.append(updated_page)

        return updated_pages

    def _generate_powerpoint(
        self,
        slide_config: SlideConfig,
        pages: list[PageDefinition],
        output_path: Path,
    ) -> Path:
        """PowerPointファイルの生成

        SlideConfigとPageDefinitionのリストを使用して、
        PowerPointGeneratorで最終的なPowerPointファイルを生成します。

        Args:
            slide_config: スライド設定
            pages: ページ定義のリスト
            output_path: 出力先パス

        Returns:
            Path: 生成されたファイルのパス

        Raises:
            PowerPointError: PowerPoint生成エラー
        """
        self.logger.debug(
            "generating_powerpoint",
            output_path=str(output_path),
            page_count=len(pages),
        )

        generator = PowerPointGenerator(slide_config)
        result_path = generator.generate(pages, output_path)

        self.logger.info(
            "powerpoint_generated",
            output_path=str(result_path),
            file_size=result_path.stat().st_size if result_path.exists() else 0,
        )

        return result_path
