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
**Status**: 🚀 **IN PROGRESS** (Foundation Implemented 2026-01-17)
**Estimated Effort**: 3.5-5 weeks (18-27 days)
**Business Value**: HIGH - Increases average order value and customer satisfaction
**📄 Detailed Planning**: See [docs/MULTI_PASSENGER_CLAIMS.md](docs/MULTI_PASSENGER_CLAIMS.md)

### Overview
...
### Implementation Phases

1. **Backend Foundation** (3-5 days): Database models, repositories, services ✅
2. **Single Claim Group API** (2-3 days): Core API endpoints ⏳
3. **Frontend Multi-Passenger Form** (5-7 days): Wizard with passenger addition ✅ (Step 3 Refactored)
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
