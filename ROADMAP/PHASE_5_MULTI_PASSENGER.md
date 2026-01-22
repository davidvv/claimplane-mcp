## Phase 5: Multi-Passenger Claims (Family/Group Claims)

**Priority**: HIGH - Major UX improvement and revenue opportunity
**Status**: 🚀 **IN PROGRESS** - ~40% Complete
**Estimated Effort**: 3.5-5 weeks (18-27 days)
**Business Value**: HIGH - Increases average order value and customer satisfaction
**📄 Detailed Planning**: See [docs/MULTI_PASSENGER_CLAIMS.md](docs/MULTI_PASSENGER_CLAIMS.md)

### Latest Major Progress (2026-01-22)
- ✅ **Draft Claim Continuation Fix**: Fixed magic link resume flow with full form pre-fill (Task #289).
- ✅ **Digital POA Signature System**: Implemented "no-scan" authorization flow.
- ✅ **Signature Pad Component**: Reusable React component for drawing signatures.
- ✅ **Dynamic PDF Generation**: Backend service to "stamp" signatures onto legal templates.
- ✅ **Email Integration**: Auto-attach signed documents to confirmation emails.
- ✅ **Smart Notification Configuration**: Pre-approved path for RocketChat notifications.

### Implementation Phases

1. **Backend Foundation** (3-5 days): Database models, repositories, services ✅
2. **Legal & Authorization Flow** (3-4 days): Digital POA signature, PDF generation, Email attachments ✅
3. **Single Claim Group API** (2-3 days): Core API endpoints ✅ (Enhanced for draft resume)
4. **Frontend Multi-Passenger Form** (5-7 days): Wizard with passenger addition ✅ (Step 3 Refactored & Draft Resume fixed)
5. **Customer Dashboard** (2-3 days): View grouped claims ⏳
6. **Admin Interface** (4-6 days): Manage and process grouped claims ⏳
7. **Notifications & Polish** (2-3 days): Email templates, testing ✅ (Draft resume flow verified)

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
