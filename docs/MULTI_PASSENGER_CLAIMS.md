# Multi-Passenger Claims Feature

## Overview

Allow a single account holder (e.g., a parent) to submit multiple related claims for different passengers (e.g., family members) on the same flight, while maintaining individual claim processing and providing administrative benefits through claim grouping.

## Business Requirements

### User Story
**As a** account holder (customer)
**I want to** submit compensation claims for multiple family members on the same flight
**So that** I can manage all claims from one account without creating separate accounts for each family member

### Admin Story
**As an** administrator
**I want to** view related claims grouped together
**So that** I can process family claims more efficiently and avoid duplicating work

## Use Cases

### Primary Use Case: Family Travel Claims
- Parent books flight for family of 4 (2 adults, 2 children)
- Flight is delayed/cancelled, all 4 passengers eligible for compensation
- Parent submits 4 separate claims from their account
- Each claim has same flight info but different passenger details
- Parent receives 4x compensation (€250-€600 per passenger depending on distance)

### Secondary Use Cases
- Business traveler booking for colleagues
- Travel agent managing claims for clients
- Group organizer filing for tour participants

## Technical Architecture

### Data Model Changes

#### New Table: `claim_groups`
```sql
CREATE TABLE claim_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_holder_id UUID NOT NULL REFERENCES customers(id),
    flight_number VARCHAR(10) NOT NULL,
    flight_date DATE NOT NULL,
    group_name VARCHAR(255),  -- e.g., "Smith Family - AB1234"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Modified Table: `claims`
```sql
ALTER TABLE claims
ADD COLUMN claim_group_id UUID REFERENCES claim_groups(id),
ADD COLUMN passenger_first_name VARCHAR(100) NOT NULL,
ADD COLUMN passenger_last_name VARCHAR(100) NOT NULL,
ADD COLUMN passenger_date_of_birth DATE,
ADD COLUMN relationship_to_holder VARCHAR(50);  -- 'self', 'spouse', 'child', 'parent', 'other'
```

#### New Table: `claim_group_notes`
```sql
CREATE TABLE claim_group_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_group_id UUID NOT NULL REFERENCES claim_groups(id),
    admin_id UUID NOT NULL REFERENCES customers(id),
    note_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Backend Changes

#### New Endpoints

**POST /api/v1/claim-groups**
- Create a new claim group
- Returns claim_group_id for subsequent claims

**POST /api/v1/claims/grouped**
- Submit a claim with claim_group_id
- Links claim to existing group

**GET /api/v1/claim-groups/{group_id}**
- Retrieve all claims in a group
- Returns aggregated status, total compensation

**GET /api/v1/customers/me/claim-groups**
- List all claim groups for current customer
- Includes summary of claims per group

**Admin Endpoints:**
- **GET /api/v1/admin/claim-groups** - List all claim groups with filters
- **GET /api/v1/admin/claim-groups/{group_id}** - Get group details with all claims
- **POST /api/v1/admin/claim-groups/{group_id}/notes** - Add admin notes to group
- **PUT /api/v1/admin/claim-groups/{group_id}/bulk-action** - Update all claims in group

#### Business Logic Changes

**ClaimService Updates:**
- `create_grouped_claim()` - Handle claim creation with group association
- `get_claims_by_group()` - Retrieve all claims in a group
- `calculate_group_total_compensation()` - Sum compensation for all group claims

**ClaimGroupService (New):**
- `create_claim_group()` - Initialize new claim group
- `add_claim_to_group()` - Associate claim with group
- `get_group_summary()` - Aggregated stats for admin view
- `bulk_update_group_claims()` - Apply same action to all claims

**Validation Rules:**
- All claims in group must have same flight_number and flight_date
- Account holder can only manage their own claim groups
- Passenger details must be unique within a group (no duplicate passengers)

### Frontend Changes

#### New UI Components

**Step 0: Claim Type Selection (New)**
```
┌─────────────────────────────────────┐
│ Who is this claim for?              │
│                                     │
│ ○ Just me (single claim)           │
│ ○ Multiple passengers (family)     │
│                                     │
│ [Continue]                          │
└─────────────────────────────────────┘
```

**Multi-Passenger Wizard:**
1. **Flight Details** (same as current Step 1)
2. **Eligibility Check** (same as current Step 2)
3. **Account Holder Info** (pre-populated, one-time)
4. **Add Passengers** (new, repeatable)
   - First/Last Name
   - Date of Birth
   - Relationship to you
   - Copy address checkbox (default checked)
   - Upload documents per passenger
   - [+ Add Another Passenger] button
5. **Review All Claims** (new, group summary)
   - Shows all passengers
   - Total compensation estimate
   - Group submission

**Customer Dashboard Updates:**
- Add "Claim Groups" tab
- Show grouped claims with expandable rows
- Display group totals and shared flight info

**Admin Dashboard Updates:**
- Add "Claim Groups" view
- Filter by group status (all pending, all approved, mixed, etc.)
- Bulk action buttons (approve all, request info from all)
- Group notes section

#### Modified Pages

**ClaimFormPage.tsx:**
- Add initial step for single vs. multi-passenger selection
- Conditional rendering based on claim type
- New state management for multiple passengers

**New Pages:**
- `MultiPassengerClaimForm.tsx` - Wizard for grouped claims
- `ClaimGroupDetailsPage.tsx` - Customer view of grouped claims
- `AdminClaimGroupsPage.tsx` - Admin management interface

## User Experience Flow

### Customer Flow: Multi-Passenger Submission

1. **Start Claim**
   - User clicks "File New Claim"
   - Sees option: "Single passenger" or "Multiple passengers"
   - Selects "Multiple passengers"

2. **Flight & Eligibility** (Steps 1-2, unchanged)
   - Enter flight details
   - Check eligibility
   - System confirms all passengers on flight eligible

3. **Account Holder Info** (Step 3, one-time)
   - Pre-populated from profile
   - User confirms/updates address
   - This address shared by default with all passengers

4. **Add Passengers** (Step 4, repeatable)
   ```
   Passenger 1 of 4
   ─────────────────
   First Name: [John]
   Last Name:  [Smith]
   Date of Birth: [01/15/1975]
   Relationship: [Self ▼]

   ☑ Same address as account holder

   Documents:
   [Upload boarding pass] [Upload ID]

   ───────────────────────
   [+ Add Another Passenger]  [Continue to Next]
   ```

5. **Review & Submit** (Step 5)
   ```
   Flight AB1234 - May 15, 2025
   4 passengers

   ┌─────────────────────────────────────┐
   │ 1. John Smith (Self)          €600  │
   │ 2. Jane Smith (Spouse)        €600  │
   │ 3. Emily Smith (Child)        €600  │
   │ 4. Michael Smith (Child)      €600  │
   └─────────────────────────────────────┘

   Total Compensation: €2,400

   Group Name: Smith Family - AB1234 (auto-generated)

   [Submit All Claims]
   ```

6. **Confirmation**
   - Shows 4 individual claim IDs
   - Shows claim group ID
   - Email sent with all claim references

### Admin Flow: Grouped Claim Processing

1. **Dashboard View**
   ```
   Claim Groups (12 pending)

   Group ID    Flight      Passengers  Status         Total
   ─────────────────────────────────────────────────────────
   CG-001      AB1234      4          3 pending,     €2,400
                                      1 approved
   CG-002      XY5678      2          All pending    €1,200
   ```

2. **Group Detail View**
   - See all 4 claims in expandable list
   - Each claim has individual status
   - Shared flight information displayed once
   - Bulk action buttons: "Approve All", "Request Info from All"

3. **Efficiency Benefits**
   - Upload eligibility documents once for the flight
   - Copy notes to all claims in group
   - Process all claims with single approval
   - Flag issues across all passengers at once

## Implementation Phases

### Phase 1: Backend Foundation
**Estimated Effort:** 3-5 days

- Create database migrations for new tables
- Implement ClaimGroup model and repository
- Add ClaimGroupService with core business logic
- Create API endpoints for claim group management
- Write unit tests for grouping logic

**Deliverables:**
- Working API for creating and managing claim groups
- Documentation for new endpoints

### Phase 2: Single Claim Group Creation
**Estimated Effort:** 2-3 days

- Update claim submission flow to accept optional claim_group_id
- Add validation for grouped claims
- Implement group summary calculations
- Test grouped claim creation via API

**Deliverables:**
- Ability to create grouped claims via API
- Postman/curl examples

### Phase 3: Frontend - Multi-Passenger Form
**Estimated Effort:** 5-7 days

- Create initial claim type selection step
- Build multi-passenger wizard component
- Implement passenger addition/removal UI
- Add group review and submission
- Handle document uploads per passenger

**Deliverables:**
- Working multi-passenger claim submission form
- Customer can file grouped claims

### Phase 4: Customer Dashboard
**Estimated Effort:** 2-3 days

- Add "Claim Groups" section
- Display grouped claims with expansion
- Show group totals and status summary
- Link to individual claim details

**Deliverables:**
- Customer can view their claim groups
- Navigate between group and individual views

### Phase 5: Admin Interface
**Estimated Effort:** 4-6 days

- Create admin claim groups list view
- Build group detail page with all claims
- Implement bulk action functionality
- Add group notes feature
- Update filters to include grouped claims

**Deliverables:**
- Admin can efficiently process grouped claims
- Bulk actions working
- Group notes functional

### Phase 6: Notifications & Polish
**Estimated Effort:** 2-3 days

- Update email templates for grouped claims
- Send group confirmation emails
- Add notification when any claim in group updates
- Polish UI/UX based on testing
- Performance optimization

**Deliverables:**
- Complete notification system
- Production-ready feature

**Total Estimated Effort:** 18-27 days (3.5-5 weeks)

## Business Value

### Customer Benefits
- **Convenience:** Submit all family claims at once
- **Efficiency:** Don't re-enter same flight details
- **Organization:** Track all claims together
- **Time Savings:** 75% reduction in data entry for 4-person family

### Company Benefits
- **Processing Efficiency:** Review flight eligibility once for all passengers
- **Reduced Errors:** Shared data means consistency across claims
- **Customer Satisfaction:** Better UX = higher completion rates
- **Revenue Protection:** Easier to catch fraud (e.g., fake family members)
- **Competitive Advantage:** Most competitors don't offer this feature

### Financial Impact
- **Increased Conversions:** Families more likely to complete claims
- **Higher Average Order Value:** 4 claims instead of 1
- **Reduced Support Costs:** Fewer questions about linking claims
- **Estimated Revenue Increase:** 15-25% from family travelers

## Technical Considerations

### Performance
- Bulk operations must be atomic (all succeed or all fail)
- Group queries need proper indexing on claim_group_id
- Document uploads parallelized for multiple passengers

### Security
- Verify account holder owns all claims in group
- Prevent unauthorized access to grouped claim details
- Audit log all bulk actions
- Rate limiting on group creation (prevent abuse)

### Edge Cases
- What if one passenger's claim is rejected but others approved?
- How to handle partial group cancellations?
- Can passengers be added to group after initial submission?
- What if passengers have different addresses (e.g., divorced parents)?

### Proposed Solutions
1. **Partial Approval:** Each claim maintains independent status
2. **Partial Cancellation:** Allow individual claim cancellation, group remains
3. **Adding Passengers:** Not allowed after submission (create new group instead)
4. **Different Addresses:** Override address per passenger with checkbox

## Data Privacy & Compliance

### GDPR Considerations
- Account holder is data controller for family members
- Must obtain consent to submit claims on behalf of others
- Add consent checkbox: "I confirm I have permission to file claims for these passengers"
- Allow passengers to claim ownership of their claim later (if they create account)

### Data Retention
- Grouped claims follow same retention policy as individual claims
- Deleting account holder should NOT delete passenger claims
- Transfer ownership to passengers if they register

## Testing Requirements

### Unit Tests
- ClaimGroupService methods
- Validation rules for grouped claims
- Compensation calculations

### Integration Tests
- End-to-end group submission
- Bulk admin actions
- Group query performance

### User Acceptance Testing
- Submit claims for 2, 3, 4, 5+ passengers
- Admin processes grouped claims
- Edge cases (partial approval, cancellation)

### Load Testing
- 100 concurrent group submissions
- Bulk update 50 claims at once
- Dashboard with 1000+ claim groups

## Open Questions

1. **Maximum Group Size:** Limit to 10 passengers? (Reasonable for family/small group)
2. **Group Naming:** Auto-generate or let user customize?
3. **Payment Splitting:** Should we support different bank accounts per passenger?
4. **Historical Migration:** Can customers group existing claims retroactively?
5. **Pricing Impact:** Charge per claim or per group? (Currently: no direct charge, commission-based)

## Success Metrics

### Adoption Metrics
- % of claims submitted as grouped vs. single
- Average passengers per group
- Completion rate for multi-passenger vs. single claims

### Efficiency Metrics
- Admin processing time: grouped vs. individual
- Support tickets related to family claims
- Error rate for grouped claims

### Business Metrics
- Revenue per customer (should increase)
- Customer lifetime value
- Claim completion rates

### Targets (6 months post-launch)
- 20% of claims submitted as grouped
- 30% reduction in admin processing time for family claims
- 25% increase in average compensation per customer
- 95% completion rate for grouped claim flow

## Documentation Requirements

### User-Facing
- Help article: "How to file claims for family members"
- FAQ: "Can I submit claims for my family?"
- Video tutorial: Multi-passenger submission

### Internal
- API documentation for claim groups
- Admin guide: Processing grouped claims
- Database schema documentation

## Future Enhancements (Beyond Initial Release)

### Phase 2 Features
- **Claim Templates:** Save passenger details for future trips
- **Family Profiles:** Pre-configure family members in account settings
- **Smart Grouping:** Auto-suggest grouping if similar claims detected
- **Split Payments:** Different bank accounts per passenger
- **Group Chat:** Communication thread for all passengers in group
- **Retroactive Grouping:** Link existing claims into a group

### Integration Ideas
- Import passenger data from booking confirmations
- Integration with airline APIs to fetch passenger manifest
- Bulk upload via CSV for travel agents

---

## Next Steps

1. **Review & Validate:** Product team reviews this document
2. **Prioritization:** Decide when to implement (after Phase 3? After launch?)
3. **Design Mockups:** Create detailed UI designs for multi-passenger flow
4. **Technical Spike:** Investigate database performance for grouped queries
5. **User Research:** Interview customers about family travel claims
6. **Cost Analysis:** Estimate development cost vs. expected revenue

---

**Document Status:** Planning
**Target Implementation:** Post-MVP (Phase 5 or 6)
**Priority:** High (significant UX improvement and revenue opportunity)
**Last Updated:** 2025-12-08
