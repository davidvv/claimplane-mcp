# Digital Power of Attorney (POA) Signature - Implementation Plan

## Overview
This document outlines the implementation plan for adding a digital signature system to collect legally valid Powers of Attorney from customers without requiring them to scan and upload documents.

**Status:** Planning Complete - Ready for Implementation  
**Created:** 2026-01-20  
**OpenProject WPs:** #206-#216

---

## Business Objectives

1. **Eliminate Friction:** Remove the "scan and upload" barrier that causes customer drop-off
2. **Legal Compliance:** Ensure POA is legally valid under EU (eIDAS) and US (ESIGN Act) regulations
3. **Industry Standard:** Match competitor flows (AirHelp, Flightright) for seamless UX
4. **Mandatory Requirement:** POA is legally required for us to act as customer's representative

---

## Architecture Overview

### New Claim Wizard Flow
```
Step 1: Flight Details
   ↓
Step 2: Eligibility Check
   ↓
Step 3: Passenger Information
   ↓
Step 4: Authorization (POA Signature) ← NEW STEP
   ↓
Step 5: Review & Submit
```

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                            │
│  - SignaturePad.tsx (react-signature-canvas)                        │
│  - Step4_Authorization.tsx (POA signature page)                     │
│  - ClaimFormPage.tsx (updated wizard controller)                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ POST /claims/{id}/sign-poa
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI)                           │
│  - app/routers/claims.py (API endpoint)                             │
│  - app/services/poa_service.py (PDF generation)                     │
│  - app/services/file_service.py (Nextcloud upload)                  │
│  - app/services/claim_verification_service.py (POA check)           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         STORAGE                                     │
│  - Nextcloud: Signed POA PDF                                        │
│  - PostgreSQL: ClaimFile record (type: power_of_attorney)           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Work Packages

### Phase 1: Design & Templates (WP #206-207)
| WP | Subject | Estimated | Status |
|----|---------|-----------|--------|
| 206 | Create ClaimPlane vector logo and branding | 3-4 hours | New |
| 207 | Create POA PDF template with legal text | 4-6 hours | New |

### Phase 2: Backend Implementation (WP #208-209, #213-214)
| WP | Subject | Estimated | Status |
|----|---------|-----------|--------|
| 208 | Implement POA Service for PDF generation | 6-8 hours | New |
| 209 | Create /sign-poa API endpoint and schemas | 3-4 hours | New |
| 213 | Update claim verification logic for POA | 1-2 hours | New |
| 214 | Attach signed POA to confirmation email | 2-3 hours | New |

### Phase 3: Frontend Implementation (WP #210-212)
| WP | Subject | Estimated | Status |
|----|---------|-----------|--------|
| 210 | Create SignaturePad component | 2-3 hours | New |
| 211 | Create Step 4 Authorization page | 6-8 hours | New |
| 212 | Integrate POA step into claim wizard | 3-4 hours | New |

### Phase 4: Testing & Documentation (WP #215-216)
| WP | Subject | Estimated | Status |
|----|---------|-----------|--------|
| 215 | E2E Testing: POA digital signature flow | 6-8 hours | New |
| 216 | Documentation: POA digital signature system | 2-3 hours | New |

**Total Estimated Development Time:** 36-50 hours (5-7 days)

---

## Technical Specifications

### Frontend Technologies
- **Library:** `react-signature-canvas` (wrapper for signature_pad)
- **Export Format:** PNG (base64-encoded)
- **Metadata Captured:** Timestamp, browser info, device type

### Backend Technologies
- **PDF Library:** PyMuPDF (fitz) - Fast, powerful PDF manipulation
- **Storage:** Nextcloud (existing infrastructure)
- **Document Type:** `power_of_attorney` (added to ClaimFile model)

### Legal Compliance
- **EU (eIDAS):** Advanced Electronic Signature (AES)
- **US (ESIGN Act):** Electronic signature with intent and consent
- **Audit Trail:** IP address, timestamp, user agent embedded in PDF

---

## Multi-Passenger Handling

**Decision:** Primary passenger signs on behalf of all passengers

**Implementation:**
1. User selects "Primary Passenger" from dropdown (for multi-passenger claims)
2. Legal text includes consent clause: *"I confirm I am authorized to sign on behalf of all listed passengers"*
3. Checkbox required: "I have consent from all passengers"
4. For corporate bookings, company is responsible for collecting consent

**Alternative Considered:** Individual signatures for each adult
- **Rejected because:** Too complex for UX, higher drop-off rate
- **Use case:** Corporate bookings with unrelated passengers should handle internally

---

## API Specification

### POST /claims/{claim_id}/sign-poa

**Request:**
```json
{
  "signature_image": "data:image/png;base64,iVBORw0KG...",
  "signer_name": "John Doe",
  "is_primary_passenger": true,
  "consent_terms": true,
  "consent_electronic_signature": true,
  "consent_represent_all": true
}
```

**Response:**
```json
{
  "file_id": "123e4567-e89b-12d3-a456-426614174000",
  "download_url": "/files/123e4567-e89b-12d3-a456-426614174000",
  "signed_at": "2026-01-20T10:30:00Z"
}
```

### GET /claims/{claim_id}/verification

**Response (updated):**
```json
{
  "is_complete": false,
  "missing_data": [],
  "missing_documents": ["power_of_attorney"],
  "has_pnr": true,
  "has_poa": false,  ← NEW
  "can_submit": false,
  "recommendation": "Needs POA signature"
}
```

---

## User Flow (Step 4: Authorization)

1. **Entry:** User clicks "Continue" from Step 3 (Passenger Info)
2. **Display:**
   - Legal text explaining POA
   - Flight/passenger summary
   - Signature canvas
   - Consent checkboxes
3. **Action:** User draws signature with finger/mouse
4. **Validation:**
   - Signature not empty
   - All consents checked
   - Primary passenger selected (if multi-passenger)
5. **Submit:** POST to /sign-poa endpoint
6. **Success:** Navigate to Step 5 (Review)
7. **Confirmation:** Signed POA attached to email

---

## Legal Considerations

### Required Consent Checkboxes
1. ✓ "I accept the Terms of Service and Privacy Policy"
2. ✓ "I consent to use electronic signatures for this Power of Attorney"
3. ✓ "I confirm I am authorized to sign on behalf of all passengers listed" (multi-passenger only)

### Audit Trail (embedded in PDF footer)
```
Signed by: John Doe (john.doe@example.com)
IP Address: 192.168.1.100
Date/Time: 2026-01-20 10:30:00 UTC
User Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 15_0...)
```

### Legal Review Required
- POA template legal text must be reviewed by EU and US counsel
- Multi-passenger authorization clause
- eIDAS/ESIGN compliance verification

---

## Dependencies & Blockers

### Critical Dependencies
1. **Logo Design (WP #206)** → Blocks POA template creation
2. **POA Template (WP #207)** → Blocks backend implementation
3. **Backend API (WP #208-209)** → Blocks frontend integration

### External Dependencies
- Legal review of POA template (parallel track)
- PyMuPDF library (add to requirements.txt)
- react-signature-canvas package (npm install)

---

## Success Metrics

### Development KPIs
- [ ] All WPs completed and tested
- [ ] Legal review approved
- [ ] E2E tests passing (100% coverage for POA flow)
- [ ] Documentation complete

### Business KPIs (post-launch)
- Reduction in "scan and upload" drop-off rate
- POA signature completion rate
- Customer feedback on signature UX
- Legal disputes avoided (due to proper documentation)

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Legal text not compliant | High | Get legal review before production |
| PDF generation fails | Medium | Comprehensive error handling + fallback to manual upload |
| Signature not captured on mobile | High | Extensive mobile testing, touch event handling |
| Multi-passenger disputes | Medium | Clear consent language + disclaimer |
| Email delivery fails | Low | Retry logic + user can download from dashboard |

---

## Next Steps

1. **Assign WPs** to development team
2. **Start with WP #206** (Logo design) - non-blocking for other work
3. **Parallel tracks:**
   - Design: WP #206-207
   - Backend: WP #208-209
   - Frontend: WP #210
4. **Legal review:** Initiate in parallel with development
5. **Integration:** WP #211-214 (after components are ready)
6. **QA:** WP #215 (comprehensive testing)

---

## Related Documents
- `docs/research/claim_requirements.md` - Research findings on airline/competitor requirements
- OpenProject Work Packages: #204, #206-216
- User Questions Answered: 2026-01-20

---

**Plan Created By:** OpenCode (Antigravity AI)  
**Approved By:** [Pending]  
**Last Updated:** 2026-01-20
