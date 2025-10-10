# Frontend PDF Download Integration Guide

## Overview

The backend now provides a complete solution for downloading and serving research PDFs that the frontend can consume. This guide explains how to integrate PDF downloads in your React application.

## API Changes

### 1. Download Endpoint Response

**Endpoint:** `POST /research_download`

**Request Body:**
```json
{
  "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
  "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
  "title": "Optional Paper Title"
}
```

**Response (Updated):**
```json
{
  "output_path": "/absolute/path/to/file.pdf",  // Server-side path (for logging)
  "download_url": "/research/files/filename.pdf",  // URL for frontend to use
  "filename": "filename.pdf"  // The actual filename
}
```

### 2. File Serving Endpoint (New)

**Endpoint:** `GET /research/files/{filename}`

**Purpose:** Serves the downloaded PDF files to the frontend

**Response:** PDF file binary data with proper headers

**Security Features:**
- Path traversal protection
- Only serves files from `output/research` directory
- Only allows PDF files
- Returns 404 if file not found

## Frontend Integration Examples

### Option 1: Direct Download Link (Recommended)

Use the `download_url` in an anchor tag for a simple download button:

```jsx
import React, { useState } from 'react';

function ResearchDownloader() {
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [filename, setFilename] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('http://your-backend-url/research_download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pdf_url: 'https://arxiv.org/pdf/2304.04949v1.pdf',
          arxiv_url: 'https://arxiv.org/abs/2304.04949v1',
          title: 'Research Paper Title'
        })
      });

      const data = await response.json();
      setDownloadUrl(data.download_url);
      setFilename(data.filename);
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleDownload} disabled={loading}>
        {loading ? 'Downloading...' : 'Prepare Download'}
      </button>
      
      {downloadUrl && (
        <a 
          href={`http://your-backend-url${downloadUrl}`}
          download={filename}
          className="download-button"
        >
          Download PDF: {filename}
        </a>
      )}
    </div>
  );
}

export default ResearchDownloader;
```

### Option 2: Fetch and Display in Browser

If you want to display the PDF in the browser (using a PDF viewer library):

```jsx
import React, { useState } from 'react';

function PDFViewer() {
  const [pdfBlob, setPdfBlob] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAndDisplayPDF = async () => {
    setLoading(true);
    
    try {
      // Step 1: Download the PDF via backend
      const downloadResponse = await fetch('http://your-backend-url/api/research_download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pdf_url: 'https://arxiv.org/pdf/2304.04949v1.pdf',
          arxiv_url: 'https://arxiv.org/abs/2304.04949v1',
          title: 'Research Paper'
        })
      });

      const { download_url } = await downloadResponse.json();

      // Step 2: Fetch the PDF file
      const pdfResponse = await fetch(`http://your-backend-url${download_url}`);
      const blob = await pdfResponse.blob();
      
      setPdfBlob(URL.createObjectURL(blob));
    } catch (error) {
      console.error('Failed to load PDF:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={fetchAndDisplayPDF} disabled={loading}>
        {loading ? 'Loading...' : 'Load PDF'}
      </button>
      
      {pdfBlob && (
        <iframe
          src={pdfBlob}
          width="100%"
          height="800px"
          title="PDF Viewer"
        />
      )}
    </div>
  );
}

export default PDFViewer;
```

### Option 3: Using React Query

For better state management and caching:

```jsx
import { useMutation } from '@tanstack/react-query';

const useDownloadPDF = () => {
  return useMutation({
    mutationFn: async (pdfData) => {
      const response = await fetch('http://your-backend-url/research_download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(pdfData)
      });
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      return response.json();
    }
  });
};

function ResearchCard({ paper }) {
  const downloadMutation = useDownloadPDF();

  const handleDownload = () => {
    downloadMutation.mutate({
      pdf_url: paper.pdf_url,
      arxiv_url: paper.arxiv_url,
      title: paper.title
    });
  };

  return (
    <div className="research-card">
      <h3>{paper.title}</h3>
      <button onClick={handleDownload} disabled={downloadMutation.isLoading}>
        {downloadMutation.isLoading ? 'Preparing...' : 'Download PDF'}
      </button>
      
      {downloadMutation.isSuccess && (
        <a 
          href={`http://your-backend-url${downloadMutation.data.download_url}`}
          download={downloadMutation.data.filename}
          className="download-link"
        >
          Click here to download: {downloadMutation.data.filename}
        </a>
      )}
      
      {downloadMutation.isError && (
        <p className="error">Download failed. Please try again.</p>
      )}
    </div>
  );
}
```

## CORS Configuration

Make sure your backend CORS settings allow the frontend domain. The `app/main.py` should have:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Response Fields Explanation

| Field | Type | Description | Usage |
|-------|------|-------------|-------|
| `output_path` | string | Absolute server path | For backend logging/debugging only |
| `download_url` | string | Relative URL path | Use this in frontend to download the file |
| `filename` | string | PDF filename | Use for display or as download filename |

## Security Considerations

1. **Path Traversal Protection**: The file serving endpoint validates that files are only served from the `output/research` directory
2. **File Type Validation**: Only PDF files are allowed
3. **CORS**: Ensure proper CORS configuration for your frontend domain
4. **Rate Limiting**: Consider adding rate limiting to prevent abuse

## Error Handling

The file serving endpoint returns these error codes:

- `404 Not Found`: File doesn't exist
- `403 Forbidden`: Attempting to access files outside allowed directory
- `400 Bad Request`: Attempting to download non-PDF files

Example error handling:

```jsx
const downloadPDF = async (downloadUrl) => {
  try {
    const response = await fetch(`http://your-backend-url${downloadUrl}`);
    
    if (response.status === 404) {
      alert('File not found. It may have been deleted.');
      return;
    }
    
    if (response.status === 403) {
      alert('Access denied to this file.');
      return;
    }
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    // ... handle the blob
  } catch (error) {
    console.error('Download error:', error);
    alert('Failed to download PDF. Please try again.');
  }
};
```

## Testing

You can test the endpoints using curl:

```bash
# 1. Download a PDF
curl -X POST http://localhost:8000/research_download \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://arxiv.org/pdf/2304.04949v1.pdf",
    "arxiv_url": "https://arxiv.org/abs/2304.04949v1",
    "title": "Test Paper"
  }'

# 2. Download the file
curl -O http://localhost:8000/research/files/Test_Paper.pdf
```

## Summary

The backend now provides:
1. ✅ PDF download and storage (`POST /research_download`)
2. ✅ PDF file serving endpoint (`GET /research/files/{filename}`)
3. ✅ Download URL for frontend consumption
4. ✅ Security features (path validation, file type checking)

The frontend should:
1. Call the download endpoint to prepare the PDF
2. Use the returned `download_url` to download or display the PDF
3. Handle errors appropriately
4. Consider caching downloaded PDFs for better UX

