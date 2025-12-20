"""Page definition models."""


from pydantic import BaseModel, Field

from slidemaker.core.models.element import ImageElement, TextElement


class PageDefinition(BaseModel):
    """Definition of a single slide page."""

    page_number: int = Field(..., ge=1, description="Page number (1-indexed)")
    title: str | None = Field(default=None, description="Optional page title")
    elements: list[TextElement | ImageElement] = Field(
        default_factory=list, description="List of elements on the page"
    )
    layout: str | None = Field(default=None, description="Optional layout template name")
    notes: str | None = Field(default=None, description="Speaker notes for this slide")
    background_color: str | None = Field(
        default=None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Optional background color override"
    )

    def add_element(self, element: TextElement | ImageElement) -> None:
        """Add an element to the page."""
        self.elements.append(element)

    def sort_elements_by_z_index(self) -> None:
        """Sort elements by z-index (bottom to top)."""
        self.elements.sort(key=lambda e: e.z_index)

    def get_text_elements(self) -> list[TextElement]:
        """Get all text elements."""
        return [e for e in self.elements if isinstance(e, TextElement)]

    def get_image_elements(self) -> list[ImageElement]:
        """Get all image elements."""
        return [e for e in self.elements if isinstance(e, ImageElement)]
