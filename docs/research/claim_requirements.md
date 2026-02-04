# Flight Compensation Claim Requirements Research

## Overview
This document summarizes the requirements for filing flight compensation claims across major airlines and industry competitors. The goal is to determine if "at least one document" is a technical or legal necessity for claim submission.

## 1. Major Airlines (Direct Claims)
Direct claims with airlines typically do not require document uploads if the customer provides a valid **Booking Reference (PNR)**. The airline uses this to verify the passenger manifest in their own systems.

| Region | Airline | Document Mandatory? | Key Data Required |
| :--- | :--- | :--- | :--- |
| **EU** | Lufthansa | No | Booking code, Flight number, Date |
| **EU** | Air France / KLM | No | Booking reference, Flight number |
| **EU** | Ryanair | Conditional | Booking ref; ID mandatory if via OTA |
| **EU** | EasyJet | No | Booking reference, Flight number |
| **EU** | British Airways | No | Booking reference, Last name |
| **US** | Delta | No | Confirmation number, Name |
| **US** | American Airlines | No | Record locator, Flight number |
| **US** | United | No | Confirmation number, Last name |
| **CA** | Air Canada | No | Booking reference, Flight number |
| **CA** | WestJet | No | Reservation code, DOB |

## 2. Competitors (Legal Representation)
Agencies acting on behalf of customers (like ClaimPlane) have different requirements because they need legal standing to represent the passenger in court or negotiations.

| Competitor | Document Mandatory? | Mandatory Documents |
| :--- | :--- | :--- |
| **AirHelp** | **Yes** | Boarding Pass/Confirmation & Signed POA |
| **Flightright** | **Yes** | Boarding Pass & Signed POA |
| **ClaimCompass** | **Yes** | Signed Power of Attorney (POA) |
| **Skycop** | **Yes** | Boarding Pass & Signed POA |
| **Refund.me** | **Yes** | Signed Power of Attorney (POA) |

## 3. Analysis for ClaimPlane
While airlines don't technically need a document to *identify* the flight, our business model (representation) requires:
1.  **Legal Authority:** A signed Power of Attorney (POA) is legally mandatory for us to act.
2.  **Evidence:** A boarding pass or booking confirmation serves as proof of contract and presence on the flight, which prevents fraudulent claims.

### Conclusion
We can potentially allow submission without a document **only if** we already have the PNR and personal details, BUT we must collect the **Power of Attorney** before we can legally process the claim. If the customer hasn't uploaded a POA, we cannot proceed.

## 4. Proposed Verification Logic
To optimize the "At least one document" rule, we should check for "Sufficient Evidence":
-   **Scenario A:** Customer provides PNR + Flight Data + Signed Digital POA (if we have an e-signature tool). -> **NO UPLOAD NEEDED.**
-   **Scenario B:** Customer provides Flight Data but NO PNR. -> **UPLOAD MANDATORY** (Boarding pass).
-   **Scenario C:** Customer has not signed a POA. -> **UPLOAD MANDATORY** (Signed PDF) or **ACTION REQUIRED** (E-sign).
