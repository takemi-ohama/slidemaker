# Getting Started with slidemaker

## Installation

### Requirements
- Python 3.13 or higher
- pip or uv package manager

### Install from PyPI

```bash
pip install slidemaker
```

### Install from Source

```bash
git clone https://github.com/yourusername/slidemaker.git
cd slidemaker

# Using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Or using pip
pip install -e .
```

## Configuration

### Environment Variables

Set your LLM API keys as environment variables:

```bash
export CLAUDE_API_KEY="your-claude-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_API_KEY="your-gemini-api-key"
```

### Configuration File

Create a `config.yaml` file:

```yaml
llm:
  composition:
    type: api
    provider: claude
    model: claude-opus-4-5
    api_key: ${CLAUDE_API_KEY}

  image_generation:
    type: api
    provider: dalle
    model: dall-e-3
    api_key: ${OPENAI_API_KEY}

output:
  directory: ./output
  temp_directory: ./tmp
  keep_temp: false

slide:
  default_size: "16:9"
  default_theme: "minimal"
```

## Basic Usage

### Create Slides from Markdown

1. Write your content in Markdown:

```markdown
# My Presentation

## Slide 1: Introduction
- Point 1
- Point 2
- Point 3

## Slide 2: Main Content
- Key message
- Supporting details
```

2. Generate PowerPoint:

```bash
slidemaker create --input presentation.md --output slides.pptx
```

### Convert from PDF

```bash
slidemaker convert --input existing.pdf --output new_slides.pptx
```

### Using a Configuration File

```bash
slidemaker create --input presentation.md --config config.yaml
```

## Command Line Options

### `slidemaker create`

Create slides from Markdown input.

Options:
- `--input, -i`: Input Markdown file (required)
- `--output, -o`: Output PowerPoint file (required)
- `--config, -c`: Configuration file path
- `--llm-config`: LLM for composition (claude-opus, gpt-5, gemini-pro)
- `--llm-image`: LLM for images (dalle-3, stable-diffusion)
- `--size`: Slide size (16:9, 4:3)
- `--theme`: Theme name

### `slidemaker convert`

Convert PDF or images to PowerPoint.

Options:
- `--input, -i`: Input PDF or directory with images (required)
- `--output, -o`: Output PowerPoint file (required)
- `--config, -c`: Configuration file path
- `--llm-config`: LLM for composition
- `--llm-image`: LLM for images

## Examples

### Minimal Example

```bash
slidemaker create -i content.md -o output.pptx --llm-config claude-opus
```

### With Custom Configuration

```bash
slidemaker create \
  --input business_report.md \
  --output Q4_report.pptx \
  --config company_config.yaml \
  --size 16:9 \
  --theme corporate
```

### PDF Conversion

```bash
slidemaker convert \
  --input old_presentation.pdf \
  --output updated_slides.pptx \
  --llm-config gemini-pro
```

## Next Steps

- Read the [Architecture Documentation](../issues/PLAN01/01_architecture.md)
- Check out [example presentations](../examples/)
- Learn about [advanced features](advanced_usage.md)
- Contribute to the project on [GitHub](https://github.com/yourusername/slidemaker)

## Troubleshooting

### Common Issues

**Problem**: `ModuleNotFoundError: No module named 'slidemaker'`
- Solution: Make sure you've installed slidemaker: `pip install slidemaker`

**Problem**: API key errors
- Solution: Verify your environment variables are set correctly

**Problem**: Permission denied when writing output
- Solution: Check you have write permissions in the output directory

For more help, see [GitHub Issues](https://github.com/yourusername/slidemaker/issues).
