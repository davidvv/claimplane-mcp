# Phase 5: Multi-Passenger Claims (Family/Group Claims)

[← Back to Roadmap](README.md)

---

**Priority**: MEDIUM
**Status**: 📋 **PLANNED**
**Estimated Effort**: 2 weeks
**Business Value**: Increases claim value and customer satisfaction
**Target Version**: v0.5.0

---


**Priority**: HIGH - Major UX improvement and revenue opportunity
**Status**: 📋 **PLANNED** - Not yet implemented
**Estimated Effort**: 3.5-5 weeks (18-27 days)
**Business Value**: HIGH - Increases average order value and customer satisfaction
**📄 Detailed Planning**: See [docs/MULTI_PASSENGER_CLAIMS.md](docs/MULTI_PASSENGER_CLAIMS.md)

### Overview

Allow a single account holder (e.g., a parent) to submit multiple related claims for different passengers (e.g., family members) on the same flight. This addresses a critical use case where families traveling together need to file separate claims while managing everything from one account.

### Business Case

**Problem**: A parent with 4 family members on a delayed flight must currently:
- Submit 4 separate claims individually
- Re-enter the same flight information 4 times
- Re-enter the same address 4 times
- Manage 4 disconnected claims

**Solution**: Multi-passenger claim submission allowing:
- One-time flight and eligibility check
- Add multiple passengers to the same claim group
- Shared account holder information
- Separate claim processing per passenger
- Grouped view for both customers and admins

**Expected Impact**:
- **Increased Conversions**: 15-25% higher completion rate for family travelers
- **Higher Average Order Value**: 4 claims instead of 1 (4x compensation)
- **Reduced Support Costs**: Fewer questions about linking claims
- **Competitive Advantage**: Most competitors don't offer this feature
- **Better Admin Efficiency**: Process family claims together, share flight eligibility verification

### Key Features

#### 5.1 Customer Features
- **Claim Type Selection**: Choose single or multi-passenger claim at start
- **Add Multiple Passengers**: Repeatable form to add each family member
  - First/Last Name
  - Date of Birth
  - Relationship (self, spouse, child, parent, other)
  - Checkbox to share address (default: checked)
  - Document upload per passenger
- **Group Management**: View all grouped claims together in dashboard
- **Shared Information**: Flight details, address entered once
- **Individual Tracking**: Each claim has own status and compensation

#### 5.2 Admin Features
- **Claim Groups View**: New admin page to view grouped claims
- **Bulk Actions**: Approve all, request info from all
- **Group Notes**: Add notes visible across all claims in group
- **Efficiency Dashboard**: See processing time savings from grouping
- **Individual Override**: Can process each claim separately if needed

#### 5.3 Database Changes
- New table: `claim_groups` (links claims together)
- New table: `claim_group_notes` (admin notes for groups)
- Modified `claims` table: Add `claim_group_id`, passenger details
- All changes backward compatible with single claims

### Success Metrics

**Adoption Metrics** (6 months post-launch):
- Target: 20% of claims submitted as grouped
- Target: Average 3 passengers per group
- Target: 95% completion rate for grouped claims

**Business Metrics**:
- Target: 25% increase in average compensation per customer
- Target: 30% reduction in admin processing time for family claims

### Implementation Phases

1. **Backend Foundation** (3-5 days): Database models, repositories, services
2. **Single Claim Group API** (2-3 days): Core API endpoints
3. **Frontend Multi-Passenger Form** (5-7 days): Wizard with passenger addition
4. **Customer Dashboard** (2-3 days): View grouped claims
5. **Admin Interface** (4-6 days): Manage and process grouped claims
6. **Notifications & Polish** (2-3 days): Email templates, testing

### GDPR & Compliance

- Account holder must confirm permission to file on behalf of others
- Consent checkbox required: "I confirm I have permission to file claims for these passengers"
- Passengers can claim ownership of their claim later if they register
- Data deletion of account holder should NOT delete passenger claims

### Technical Considerations

- All claims in group must share same flight_number and flight_date
- Passenger details must be unique within a group (no duplicates)
- Bulk operations must be atomic (all succeed or all fail)
- Each claim maintains independent status (can approve some, reject others)

### Open Questions

1. **Maximum Group Size**: Limit to 10 passengers? (Reasonable for family/small group)
2. **Group Naming**: Auto-generate (e.g., "Smith Family - AB1234") or let user customize?
3. **Payment Splitting**: Should we support different bank accounts per passenger?
4. **Historical Migration**: Can customers group existing claims retroactively?
5. **Pricing Impact**: Charge per claim or per group? (Currently: commission-based, no change needed)

### Next Steps

- [ ] Product team review and approval
- [ ] Design UI mockups for multi-passenger flow
- [ ] User research interviews with family travelers
- [ ] Technical spike on database performance
- [ ] Prioritize against other Phase 5+ features

---

## Phase 6: AeroDataBox Flight Status API Integration

---

[← Back to Roadmap](README.md)
