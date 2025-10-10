# PDF Download Solution for Frontend

## Your Question
> If I want to show FE pdf downloadable link or binary file so FE can consume (download) the pdf object. What should I add? downloadable_link: str. ???

## The Answer ✅

Yes! I've added **3 new fields** to solve this problem:

```python
class ResearchDownloadResponse(BaseModel):
    output_path: str         # Backend path (existing)
    download_url: str        # ✨ NEW: URL for frontend to download
    filename: str            # ✨ NEW: Filename of the PDF
```

## What Changed

### 1. Response Schema (`app/schemas/research.py`)
```python
class ResearchDownloadResponse(BaseModel):
    output_path: str = Field(..., description="Absolute path to the downloaded PDF file")
    download_url: str = Field(..., description="URL to download the PDF file from the server")  # NEW
    filename: str = Field(..., description="Name of the downloaded PDF file")  # NEW
```

### 2. New File Serving Endpoint (`app/routes/research.py`)
```python
@router.get("/research/files/{filename}")
def download_research_file(filename: str):
    """Serve downloaded PDF files to frontend"""
    # Returns the actual PDF file with proper headers
```

### 3. Updated Service (`app/services/research.py`)
```python
def download_research(self, research: ResearchDownload) -> ResearchDownloadResponse:
    # ... downloads PDF ...
    
    # Generate download URL for frontend
    download_url = f"/research/files/{filename}"
    
    return ResearchDownloadResponse(
        output_path=str(filepath.absolute()),
        download_url=download_url,      # ✨ NEW
        filename=filename,               # ✨ NEW
    )
```

## How Frontend Uses It

### Simple Download Button
```jsx
// 1. Download via backend
const response = await fetch('http://localhost:8000/research_download', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    pdf_url: paper.pdf_url,
    arxiv_url: paper.arxiv_url,
    title: paper.title
  })
});

const data = await response.json();

// 2. Use the download_url in your React component
<a 
  href={`http://localhost:8000${data.download_url}`}
  download={data.filename}
>
  Download PDF: {data.filename}
</a>
```

### Display PDF in Browser
```jsx
// Fetch the PDF to display
const pdfResponse = await fetch(`http://localhost:8000${data.download_url}`);
const blob = await pdfResponse.blob();
const pdfUrl = URL.createObjectURL(blob);

// Show in iframe or PDF viewer
<iframe src={pdfUrl} width="100%" height="800px" />
```

## API Flow

```
Frontend                    Backend
   |                           |
   |  POST /research_download  |
   |-------------------------->|
   |  { pdf_url, arxiv_url }  |
   |                           |
   |                           | Downloads PDF
   |                           | Saves to output/research/
   |                           |
   |  Response                 |
   |<--------------------------|
   | {                         |
   |   "output_path": "...",   |
   |   "download_url": "/research/files/paper.pdf",  ← Use this!
   |   "filename": "paper.pdf" |
   | }                         |
   |                           |
   |  GET /research/files/paper.pdf
   |-------------------------->|
   |                           |
   |  PDF Binary Data          |
   |<--------------------------|
   |  (application/pdf)        |
   |                           |
```

## Example Response

```json
{
  "output_path": "/Users/chihosong/sk/tech11-be/output/research/Intelligent_humanoids_in_manufacturing.pdf",
  "download_url": "/research/files/Intelligent_humanoids_in_manufacturing.pdf",
  "filename": "Intelligent_humanoids_in_manufacturing.pdf"
}
```

## Security Features ✅

- ✅ Path traversal protection
- ✅ Only serves files from `output/research/` directory
- ✅ Only allows PDF files
- ✅ Returns 404 if file doesn't exist
- ✅ CORS enabled for localhost:3000

## Quick Test

```bash
# Test the download endpoint
curl -X POST http://localhost:8000/research_download \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
    "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
    "title": "Test Paper"
  }'

# Test the file serving endpoint
curl -O http://localhost:8000/research/files/Test_Paper.pdf
```

## Summary

**What you asked for:** A way for the frontend to download PDFs

**What was added:**
1. ✅ `download_url`: URL path the frontend can use (e.g., `/research/files/paper.pdf`)
2. ✅ `filename`: The actual filename for display/download
3. ✅ New endpoint `/research/files/{filename}` that serves the PDF with proper headers

**Frontend usage:** Simply append the `download_url` to your backend base URL and use it in an `<a>` tag or `fetch()` call!

For complete examples and best practices, see `FRONTEND_PDF_DOWNLOAD_GUIDE.md`.

