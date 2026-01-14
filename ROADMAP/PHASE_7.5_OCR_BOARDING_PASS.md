# Phase 7.5: OCR Boarding Pass Data Extraction (ClaimPlane)

[← Back to Roadmap](README.md)

---

**Status**: ✅ **COMPLETED**
**Priority**: HIGH - Improves customer experience significantly
**Target**: v0.5.0
**Timeline**: 2026-01-13 to 2026-01-17 (This Week)
**Completed**: 2026-01-14
**Business Value**: Reduces friction in ClaimPlane's claim submission process by 80%+

---

## Overview

Implement OCR (Optical Character Recognition) to automatically extract flight details from boarding pass images, minimizing manual data entry and improving user experience.

### Business Impact

- **Reduced Abandonment**: Simplify claim submission from ~10 fields to 1 file upload
- **Higher Conversion**: Remove friction in the funnel
- **Better Data Quality**: Eliminate typos and manual entry errors
- **Faster Submissions**: Complete claim in under 60 seconds

### User Flow

**Before OCR:**
```
Customer manually enters:
1. Departure airport (IATA code)
2. Arrival airport (IATA code)
3. Flight number
4. Flight date
5. Departure time
6. Arrival time
7. Passenger name (must match boarding pass)
... then uploads boarding pass for verification
```

**After OCR:**
```
Customer:
1. Uploads boarding pass
   ↓
System extracts all data automatically
   ↓
Customer reviews pre-filled form (can edit if needed)
   ↓
Submits claim
```

---

## Technical Requirements

### 1. OCR Engine Selection

**Recommended Options:**

**Option A: Tesseract OCR (Open Source)**
- ✅ Free and open source
- ✅ High accuracy for Latin text
- ✅ Can run locally or in Docker
- ✅ Active development
- ⚠️ Requires preprocessing for best results
- **Library**: `pytesseract` (Python wrapper)

**Option B: Google Cloud Vision API**
- ✅ State-of-the-art accuracy
- ✅ Handles rotated/skewed images
- ✅ Built-in text detection & document analysis
- ⚠️ Requires API key
- ⚠️ Usage costs (~$1.50 per 1000 requests)
- **Library**: `google-cloud-vision`

**Option C: Amazon Textract**
- ✅ Excellent for structured documents
- ✅ Can detect forms and tables
- ⚠️ AWS account required
- ⚠️ Usage costs (~$1.50 per 1000 pages)

**Recommendation**: Start with **Tesseract** for MVP, add cloud options later if needed.

---

### 2. Backend Implementation

#### File: `app/services/ocr_service.py`

```python
class OCRService:
    """
    Extract flight data from boarding pass images.
    """

    async def extract_boarding_pass_data(
        self,
        file_path: str,
        preprocessing: bool = True
    ) -> Dict[str, Any]:
        """
        Extract flight details from boarding pass image.

        Returns:
        {
            "flight_number": "LH123",
            "departure_airport": "FRA",
            "arrival_airport": "JFK",
            "flight_date": "2024-01-15",
            "departure_time": "10:30",
            "passenger_name": "DOE/JOHN MR",
            "booking_reference": "ABC123",
            "confidence_scores": {...}
        }
        """
        pass

    async def preprocess_image(self, image: Image) -> Image:
        """
        Enhance image quality for better OCR:
        - Convert to grayscale
        - Adjust contrast
        - Denoise
        - Deskew (straighten rotated images)
        """
        pass

    def parse_boarding_pass_text(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse extracted text using pattern matching.

        Common patterns:
        - Flight number: /[A-Z]{2}\d{1,4}/
        - Airport codes: /[A-Z]{3}/
        - Date: Various formats (DD/MM/YYYY, DD.MM.YY, etc.)
        - Time: HH:MM format
        - Booking ref: 6-char alphanumeric
        """
        pass

    def validate_extracted_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate extracted data:
        - Airport codes exist in database
        - Flight number format is valid
        - Date is not in far past/future
        - Required fields present

        Returns: (is_valid, errors)
        """
        pass
```

#### File: `app/schemas/ocr_schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class BoardingPassData(BaseModel):
    flight_number: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    flight_date: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    passenger_name: Optional[str] = None
    booking_reference: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=1.0)

class OCRResponse(BaseModel):
    success: bool
    data: Optional[BoardingPassData] = None
    raw_text: str
    errors: List[str] = []
    warnings: List[str] = []
```

#### New Endpoint: `POST /api/claims/ocr-boarding-pass`

```python
@router.post("/ocr-boarding-pass", response_model=OCRResponse)
async def extract_boarding_pass_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    ocr_service: OCRService = Depends()
):
    """
    Upload boarding pass image and extract flight details via OCR.

    Accepts: JPEG, PNG, PDF
    Returns: Extracted data with confidence scores
    """
    # 1. Validate file type (JPEG, PNG, PDF)
    # 2. Save to temp location
    # 3. Run OCR extraction
    # 4. Parse and validate data
    # 5. Return structured response
    # 6. Clean up temp file
    pass
```

---

### 3. Frontend Implementation

#### File: `frontend_Claude45/src/components/BoardingPassUpload.tsx`

**New Component:**
```tsx
import { useState } from 'react';
import { uploadBoardingPass, extractOCRData } from '../api/claims';

export function BoardingPassUpload({ onDataExtracted }) {
  const [uploading, setUploading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState(null);

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    try {
      // Upload and extract
      const response = await extractOCRData(file);

      if (response.success) {
        setExtractedData(response.data);
        onDataExtracted(response.data);
      } else {
        setError(response.errors.join(', '));
      }
    } catch (err) {
      setError('Failed to extract data. Please enter details manually.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="boarding-pass-upload">
      <h3>Upload Boarding Pass</h3>
      <p>We'll automatically extract your flight details</p>

      <FileDropzone
        onFileSelect={handleFileUpload}
        accept="image/jpeg,image/png,application/pdf"
        loading={uploading}
      />

      {extractedData && (
        <ExtractedDataPreview
          data={extractedData}
          onEdit={() => setExtractedData(null)}
        />
      )}

      {error && (
        <ErrorMessage>
          {error}
          <button onClick={() => setError(null)}>Enter manually</button>
        </ErrorMessage>
      )}
    </div>
  );
}
```

#### Updated Flow: `ClaimSubmissionForm.tsx`

```tsx
// Add OCR step at the beginning
<Step1: Upload Boarding Pass (OCR)>
  ↓ (auto-extracted data)
<Step2: Review & Edit Details>
  ↓
<Step3: Personal Information>
  ↓
<Step4: Upload Additional Documents>
  ↓
<Step5: Bank Details>
  ↓
<Submit>
```

---

### 4. Database Schema

**No new tables required** - extracted data populates existing `Claim` fields.

Optional: Add tracking field to `claims` table:
```sql
ALTER TABLE claims
ADD COLUMN ocr_extracted BOOLEAN DEFAULT FALSE;

ALTER TABLE claims
ADD COLUMN ocr_confidence_score FLOAT;
```

---

## Implementation Plan

### Phase 1: Backend OCR Service (Day 1-2)

1. ✅ Install dependencies
   ```bash
   pip install pytesseract pillow opencv-python-headless
   # System: apt-get install tesseract-ocr tesseract-ocr-eng
   ```

2. ✅ Create `OCRService` with Tesseract integration
3. ✅ Implement image preprocessing pipeline
4. ✅ Create boarding pass text parser with regex patterns
5. ✅ Add validation logic for extracted data
6. ✅ Create new API endpoint `/api/claims/ocr-boarding-pass`
7. ✅ Write unit tests for OCR service

### Phase 2: Frontend Integration (Day 2-3)

1. ✅ Create `BoardingPassUpload` component
2. ✅ Add drag-and-drop file upload UI
3. ✅ Implement loading states and progress indicators
4. ✅ Create extracted data preview component
5. ✅ Update claim submission form to include OCR step
6. ✅ Add manual fallback option
7. ✅ Handle OCR errors gracefully

### Phase 3: Testing & Refinement (Day 3-4)

1. ✅ Test with real boarding passes (multiple airlines)
2. ✅ Measure accuracy rates
3. ✅ Fine-tune regex patterns based on results
4. ✅ Add support for PDF boarding passes
5. ✅ Optimize image preprocessing parameters
6. ✅ Performance testing (response time < 5 seconds)

### Phase 4: Documentation & Deployment (Day 4-5)

1. ✅ Update API documentation
2. ✅ Create user guide for boarding pass upload
3. ✅ Update Docker configuration (add tesseract)
4. ✅ Deploy to staging
5. ✅ QA testing
6. ✅ Deploy to production

---

## Technical Considerations

### Image Processing Pipeline

```
Raw Image
   ↓
Convert to Grayscale
   ↓
Adjust Contrast (CLAHE)
   ↓
Denoise (Gaussian blur)
   ↓
Deskew (straighten rotation)
   ↓
Binarization (black & white)
   ↓
OCR (Tesseract)
   ↓
Text Extraction
   ↓
Pattern Matching (Regex)
   ↓
Validation
   ↓
Structured Data
```

### Regex Patterns for Parsing

```python
PATTERNS = {
    "flight_number": r"\b([A-Z]{2}|[A-Z]\d|\d[A-Z])\s*\d{1,4}\b",
    "airport_code": r"\b[A-Z]{3}\b",
    "date": r"\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}",
    "time": r"\d{1,2}:\d{2}",
    "booking_ref": r"\b[A-Z0-9]{6}\b",
    "passenger": r"([A-Z]+/[A-Z]+\s+(MR|MS|MRS|DR))",
}
```

### Error Handling

**Low Confidence Score** (< 70%):
- Show warning to user
- Suggest manual review
- Allow editing of pre-filled data

**OCR Failure**:
- Fallback to manual entry
- Log error for debugging
- Show user-friendly message

**Invalid Data**:
- Highlight problematic fields
- Show validation errors
- Allow user correction

---

## Success Metrics

**Technical Metrics:**
- OCR accuracy: > 85% for key fields
- Response time: < 5 seconds per image
- Error rate: < 10% of submissions

**Business Metrics:**
- Claim submission time: Reduced by 60%+
- Form abandonment rate: Reduced by 40%+
- Data entry errors: Reduced by 70%+

---

## Rollout Strategy

### Phase 1: Opt-in Beta (Week 1)
- Add "Upload boarding pass" option alongside manual entry
- A/B test with 20% of users
- Collect accuracy feedback

### Phase 2: Default Flow (Week 2)
- Make OCR the primary submission method
- Keep manual entry as fallback
- Monitor support tickets

### Phase 3: Optimization (Ongoing)
- Improve regex patterns based on real data
- Add support for more boarding pass formats
- Consider cloud OCR for low-confidence cases

---

## Dependencies

**Python Packages:**
```txt
pytesseract==0.3.10
pillow==10.1.0
opencv-python-headless==4.8.1.78
```

**System Requirements:**
```bash
# Ubuntu/Debian
apt-get install tesseract-ocr tesseract-ocr-eng

# Docker
FROM python:3.11-slim
RUN apt-get update && apt-get install -y tesseract-ocr
```

**Frontend:**
```json
{
  "react-dropzone": "^14.2.3"
}
```

---

## Future Enhancements

1. **Multi-language Support**: Add OCR for non-English boarding passes
2. **Mobile Camera Integration**: Direct photo upload from phone camera
3. ✅ **Cloud OCR Fallback**: Use Google Vision API for low-confidence cases (Implemented)
4. **ID Document OCR**: Extract passenger details from ID cards/passports
5. **Barcode Scanning**: Extract data from boarding pass barcodes (IATA Bar Coded Boarding Pass format)

---

## Related Files

- `app/services/ocr_service.py` (new)
- `app/schemas/ocr_schemas.py` (new)
- `app/routers/claims.py` (update)
- `frontend_Claude45/src/components/BoardingPassUpload.tsx` (new)
- `frontend_Claude45/src/pages/NewClaimPage.tsx` (update)
- `requirements.txt` (update)
- `Dockerfile` (update - add tesseract)

---

[← Back to Roadmap](README.md)
