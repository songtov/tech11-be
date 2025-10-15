# Video Generation System

An AI-powered FastAPI service that generates narrated video lectures from research papers using a LangChain multi-agent pipeline.

## 🎯 Overview

This system automatically converts research papers (PDFs) into engaging video presentations with:
- **PowerPoint slides** generated from paper content
- **Narrated scripts** created by AI
- **Text-to-speech** audio generation
- **Final video** assembly with slides and narration

## 🏗️ Architecture

### Multi-Agent Pipeline

```
Research Paper (PDF)
        ↓
   Reader Agent
   (Extract content, analyze structure)
        ↓
   Slide Agent  
   (Create PowerPoint presentation)
        ↓
   Script Agent
   (Generate narration script)
        ↓
   Voice Agent
   (Convert script to audio)
        ↓
   Video Agent
   (Assemble final video)
        ↓
   Final MP4 Video
```

### Project Structure

```
app/
├── agents/                 # LangChain agents
│   ├── reader_agent.py     # PDF processing & analysis
│   ├── slide_agent.py     # PowerPoint generation
│   ├── script_agent.py    # Narration script creation
│   ├── voice_agent.py     # Text-to-speech conversion
│   └── video_agent.py     # Video assembly
├── services/
│   └── video.py           # Main orchestration service
├── routes/
│   └── video.py           # API endpoints
└── schemas/
    └── video.py           # Request/response models
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
uv sync

# Or with pip
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. Start the Server

```bash
uvicorn app.main:app --reload
```

### 4. Test the Pipeline

```bash
python test_video_pipeline.py
```

## 📡 API Usage

### Create Video from Research Paper

```bash
POST /video
Content-Type: application/json

{
  "research_id": 1
}
```

**Response:**
```json
{
  "video_url": "/output/videos/1/video_1.mp4",
  "research_id": 1,
  "duration_seconds": 120.5,
  "slide_count": 8,
  "status": "completed"
}
```

### Get Existing Video

```bash
GET /video/{research_id}
```

## 🔧 Configuration

### Agent Settings

Each agent can be configured in the `VideoService`:

```python
# Reader Agent
reader_agent = ReaderAgent(openai_api_key, model_name="gpt-4o-mini")

# Slide Agent  
slide_agent = SlideAgent(openai_api_key, model_name="gpt-4o-mini")

# Script Agent
script_agent = ScriptAgent(openai_api_key, model_name="gpt-4o-mini")

# Voice Agent
voice_agent = VoiceAgent(language="en", slow=False)

# Video Agent
video_agent = VideoAgent(fps=1, resolution=(1920, 1080))
```

### Output Directory Structure

```
output/
├── videos/
│   └── {research_id}/
│       ├── video_{research_id}.mp4      # Final video
│       ├── slides_{research_id}.pptx    # PowerPoint slides
│       ├── narration_{research_id}.mp3   # Full narration audio
│       └── slide_XX_audio.mp3          # Individual slide audio
└── research/
    └── *.pdf                            # Source research papers
```

## 🎨 Features

### Reader Agent
- **PDF text extraction** using PyMuPDF
- **Figure and table detection**
- **Paper structure analysis** with AI
- **Key section extraction** (abstract, methods, results, etc.)

### Slide Agent
- **AI-powered slide content generation**
- **Professional PowerPoint creation** with python-pptx
- **Consistent formatting** and styling
- **Educational slide structure**

### Script Agent
- **Natural narration generation**
- **TTS-optimized text processing**
- **Smooth transitions** between slides
- **Engaging educational tone**

### Voice Agent
- **Google Text-to-Speech** integration
- **Audio optimization** for video
- **Individual slide audio** generation
- **Duration calculation**

### Video Agent
- **MoviePy-based video assembly**
- **Slide-to-image conversion**
- **Audio synchronization**
- **Professional video output**

## 🛠️ Dependencies

### Core Dependencies
- `fastapi` - Web framework
- `langchain` - AI agent framework
- `langchain-openai` - OpenAI integration
- `python-pptx` - PowerPoint generation
- `moviepy` - Video processing
- `gtts` - Text-to-speech
- `pymupdf` - PDF processing

### Optional Dependencies
- `librosa` - Audio duration analysis
- `PIL` - Image processing for slide conversion

## 🔍 Troubleshooting

### Common Issues

1. **OpenAI API Key Missing**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

2. **PDF Files Not Found**
   - Ensure PDFs are in `/output/research/` directory
   - Check file permissions

3. **Video Generation Fails**
   - Check OpenAI API quota
   - Verify all dependencies are installed
   - Check output directory permissions

4. **Audio Issues**
   - Ensure gTTS is working
   - Check internet connection for TTS service

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance

### Typical Processing Times
- **PDF Analysis**: 10-30 seconds
- **Slide Generation**: 30-60 seconds  
- **Script Creation**: 20-40 seconds
- **Audio Generation**: 60-120 seconds
- **Video Assembly**: 30-90 seconds
- **Total**: 3-6 minutes per video

### Optimization Tips
- Use smaller PDFs for faster processing
- Limit slide count (8-12 slides recommended)
- Use shorter narration scripts
- Consider async processing for production

## 🔒 Security Considerations

- **API Key Protection**: Store OpenAI API key securely
- **File Access**: Restrict access to output directories
- **Input Validation**: Validate research_id parameters
- **Rate Limiting**: Implement API rate limiting for production

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
OPENAI_API_KEY=your-openai-key
DATABASE_URL=your-database-url
OUTPUT_DIR=/app/output
```

## 📝 License

This project is part of the Tech11 backend system.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Note**: This system requires an OpenAI API key and internet connection for TTS services.
