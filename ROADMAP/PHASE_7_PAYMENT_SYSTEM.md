# Phase 7: Payment System Integration

[← Back to Roadmap](README.md)

---

**Priority**: HIGH
**Status**: 📋 **PLANNED**
**Estimated Effort**: 3-4 weeks
**Business Value**: Critical for revenue generation
**Target Version**: v0.7.0
**Payment Provider**: Stripe (recommended)

---


**Priority**: CRITICAL - Required for revenue generation
**Status**: 📋 **PLANNED** - Not yet implemented
**Estimated Effort**: 4-6 weeks
**Business Value**: CRITICAL - Enables actual revenue flow (getting paid by airlines, paying customers)
**Last Updated**: 2025-12-29

### Overview

Implement end-to-end payment system to handle the two-way payment flow:
1. **Incoming payments**: Collect compensation from airlines
2. **Outgoing payments**: Distribute customer share of compensation

This is the final critical piece that enables the business model to function.

### Business Model Context

**Revenue Model**:
- Customer files claim through platform
- We handle claim processing and negotiation with airline
- Airline pays us compensation (e.g., €600)
- We take commission (e.g., 25% = €150)
- Customer receives their share (€450)

**Current Gap**:
- We can process claims and get airline approval
- BUT we have no way to actually receive or distribute money
- This phase closes that gap

### Key Features

#### 7.1 Incoming Payments (From Airlines)

**Payment Methods for Airlines**:
- [ ] **Bank Transfer** (primary method)
  - European SEPA transfers (most common in EU)
  - International SWIFT transfers
  - Generate payment invoices with unique reference codes
  - Track bank transfers via reference codes
  - Manual reconciliation workflow for admins

- [ ] **PayPal Business** (secondary method)
  - PayPal Business account integration
  - Invoice generation and sending
  - Automatic payment confirmation via webhooks
  - Refund handling

- [ ] **Stripe Connect** (future - for large airlines)
  - Direct bank transfers
  - ACH transfers (US airlines)
  - Automatic reconciliation

**Features**:
- [ ] Generate payment invoice when claim approved
  - Include claim details, passenger info, flight info
  - Unique invoice number and payment reference
  - QR code for payment
  - Send invoice to airline finance department (email)

- [ ] Payment tracking dashboard for admins
  - List all invoices (pending, paid, overdue)
  - Track payment status per claim
  - Aging report (30/60/90 days overdue)
  - Send automated payment reminders

- [ ] Payment reconciliation
  - Match incoming bank transfers to invoices (by reference code)
  - Manual matching interface for admins
  - Flag unmatched payments
  - Generate financial reports

#### 7.2 Outgoing Payments (To Customers)

**Payment Methods for Customers**:
- [ ] **SEPA Bank Transfer** (primary for EU customers)
  - Collect IBAN during claim submission or after approval
  - Validate IBAN format
  - Batch payment file generation (SEPA XML format)
  - Upload to bank portal or API integration
  - Track transfer status

- [ ] **PayPal** (alternative)
  - PayPal email address collection
  - PayPal Mass Payment API (send to multiple recipients)
  - Automatic confirmation
  - Lower fees than bank transfers for small amounts

- [ ] **Stripe** (future - instant payouts)
  - Stripe Payouts API
  - Instant bank transfers (24 hours)
  - Credit card payouts (for non-EU customers)

**Features**:
- [ ] Customer payment preferences
  - Select payment method during claim submission
  - Provide IBAN or PayPal email
  - Validate payment details
  - Allow updates to payment info

- [ ] Payment workflow
  - Admin approves claim → compensation calculated
  - System calculates customer share (compensation - commission)
  - Admin reviews and approves payout
  - System generates payment batch
  - Admin executes payment (manual or API)
  - Customer receives confirmation email
  - Update claim status to "paid"

- [ ] Payout dashboard
  - List pending payouts
  - Batch multiple payouts together (reduce fees)
  - Track payout status (pending, processing, completed, failed)
  - Retry failed payouts
  - Generate payout receipts for customers

#### 7.3 Financial Reporting

**Reports for Business**:
- [ ] **Revenue Dashboard**
  - Total compensation collected from airlines (monthly, yearly)
  - Total commission earned
  - Total paid to customers
  - Net revenue (commission - operational costs)
  - Outstanding invoices (money owed by airlines)
  - Outstanding payouts (money owed to customers)

- [ ] **Cash Flow Report**
  - Incoming payments timeline
  - Outgoing payments timeline
  - Cash balance projection
  - Working capital requirements

- [ ] **Accounting Export**
  - Export transactions to CSV/Excel
  - Format for accounting software (QuickBooks, Xero)
  - Tax reporting data
  - Invoice register
  - Payment register

#### 7.4 Database Schema Updates

**File**: `app/models.py` (update)

Add new models:

```python
class Invoice(Base):
    """Invoice sent to airline for compensation payment"""
    __tablename__ = "invoices"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)

    invoice_number = Column(String(50), unique=True, nullable=False)  # e.g., INV-2025-001234
    payment_reference = Column(String(100), unique=True, nullable=False)  # For bank transfer matching

    # Amounts
    compensation_amount = Column(Numeric(10, 2), nullable=False)  # Total compensation from airline
    currency = Column(String(3), default="EUR")

    # Status
    status = Column(String(50), default="pending")  # pending, sent, paid, overdue, cancelled
    sent_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=False)  # Payment deadline (e.g., 30 days)

    # Payment details
    payment_method = Column(String(50), nullable=True)  # bank_transfer, paypal, stripe
    payment_transaction_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Payout(Base):
    """Payout to customer for their share of compensation"""
    __tablename__ = "payouts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Amounts
    payout_amount = Column(Numeric(10, 2), nullable=False)  # Customer's share
    commission_amount = Column(Numeric(10, 2), nullable=False)  # Our commission
    total_compensation = Column(Numeric(10, 2), nullable=False)  # Total from airline
    currency = Column(String(3), default="EUR")

    # Payment details
    payment_method = Column(String(50), nullable=False)  # sepa_transfer, paypal, stripe
    payment_details = Column(JSON, nullable=True)  # IBAN, PayPal email, etc. (encrypted)

    # Status
    status = Column(String(50), default="pending")  # pending, approved, processing, completed, failed
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Transaction tracking
    transaction_id = Column(String(255), nullable=True)  # Bank reference, PayPal ID, Stripe ID
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PaymentReconciliation(Base):
    """Track manual payment reconciliation (matching bank transfers to invoices)"""
    __tablename__ = "payment_reconciliations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)

    # Bank statement details
    transaction_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    sender_name = Column(String(255), nullable=True)
    sender_iban = Column(String(34), nullable=True)
    reference = Column(String(255), nullable=True)  # Payment reference from bank statement

    # Matching
    matched = Column(Boolean, default=False)
    matched_by = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    matched_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Update `Claim` model:
```python
# Add to Claim model
commission_rate = Column(Numeric(5, 2), default=25.00)  # Percentage (e.g., 25.00 = 25%)
commission_amount = Column(Numeric(10, 2), nullable=True)  # Calculated commission
customer_payout_amount = Column(Numeric(10, 2), nullable=True)  # Amount to pay customer
```

#### 7.5 Commission Configuration

**File**: `app/config.py` (update)

```python
# Payment Configuration
DEFAULT_COMMISSION_RATE = Decimal(os.getenv("DEFAULT_COMMISSION_RATE", "25.00"))  # 25%
MIN_COMMISSION_RATE = Decimal(os.getenv("MIN_COMMISSION_RATE", "15.00"))  # 15%
MAX_COMMISSION_RATE = Decimal(os.getenv("MAX_COMMISSION_RATE", "35.00"))  # 35%

# Invoice settings
INVOICE_PAYMENT_TERMS_DAYS = int(os.getenv("INVOICE_PAYMENT_TERMS_DAYS", "30"))  # 30 days
INVOICE_OVERDUE_REMINDER_DAYS = int(os.getenv("INVOICE_OVERDUE_REMINDER_DAYS", "7"))  # Remind after 7 days

# Payout settings
MIN_PAYOUT_AMOUNT = Decimal(os.getenv("MIN_PAYOUT_AMOUNT", "50.00"))  # Don't pay out less than €50
PAYOUT_BATCH_ENABLED = os.getenv("PAYOUT_BATCH_ENABLED", "true").lower() == "true"

# Payment provider credentials
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Bank details for receiving payments
COMPANY_BANK_NAME = os.getenv("COMPANY_BANK_NAME", "")
COMPANY_IBAN = os.getenv("COMPANY_IBAN", "")
COMPANY_BIC = os.getenv("COMPANY_BIC", "")
```

#### 7.6 Security & Compliance

**PCI DSS Compliance**:
- ⚠️ **DO NOT store credit card details** (use Stripe for card payments)
- Encrypt sensitive payment data (IBAN, PayPal email) at rest
- Use HTTPS for all payment-related communications
- Audit log all payment operations
- Restrict payment operations to admin users only

**GDPR Compliance**:
- [ ] Inform customers how payment data is stored and used
- [ ] Allow customers to update payment details
- [ ] Delete payment details on account deletion (after retention period)
- [ ] Export payment history in GDPR data export

**Anti-Money Laundering (AML)**:
- [ ] Verify customer identity before large payouts (> €1000)
- [ ] Flag suspicious payment patterns for review
- [ ] Keep payment records for 7 years (legal requirement)

**Tax Compliance**:
- [ ] Issue invoices with VAT if applicable
- [ ] Generate annual tax reports (1099 forms for US customers)
- [ ] Track revenue for tax filing

### Testing Requirements

- [ ] Test invoice generation and sending
- [ ] Test payment reconciliation (match bank transfer to invoice)
- [ ] Test SEPA payout batch generation
- [ ] Test PayPal Mass Payment integration
- [ ] Test commission calculation accuracy
- [ ] Test minimum payout threshold
- [ ] Test failed payment retry logic
- [ ] Test overdue invoice reminders
- [ ] Load test: 100 payouts in one batch

### Success Criteria

- ✅ Invoices automatically generated when claim approved
- ✅ Bank transfers can be matched to invoices (reconciliation)
- ✅ Customers can receive payouts via SEPA or PayPal
- ✅ Commission calculated correctly for all claims
- ✅ Financial reports show revenue, payouts, and profit
- ✅ All payment operations logged in audit trail
- ✅ Payment data encrypted and GDPR compliant
- ✅ No manual spreadsheet tracking needed

### Open Questions

1. **Payment Provider**: Which provider for bank transfers?
   - **Option A**: Manual SEPA batch files (cheapest, requires bank portal access)
   - **Option B**: Stripe Payouts API (automated, €0.25/payout + 0.25%)
   - **Option C**: Wise API (international transfers, competitive rates)
   - **Recommendation**: Start with manual SEPA, migrate to Stripe as volume grows

2. **Commission Variability**: Should commission rate vary by claim value or airline?
   - **Recommendation**: Fixed 25% initially, add tiered pricing later (Phase 8)

3. **Payout Threshold**: Minimum payout amount to reduce transaction costs?
   - **Recommendation**: €50 minimum (batch small payouts monthly)

4. **Currency Support**: Support USD, GBP, or EUR only?
   - **Recommendation**: EUR only initially (most EU airlines), add others in Phase 8

5. **Escrow Account**: Hold customer funds in escrow until payout?
   - **Recommendation**: Yes (legal requirement in some EU countries, build trust)

### Dependencies

- **Phase 1 Complete**: Admin dashboard and claim workflow
- **Phase 3 Complete**: Authentication and authorization
- **Phase 4 Complete**: Account settings (payment details)
- **Business Setup**: Company bank account, PayPal Business account
- **Legal Setup**: Payment processing agreements, terms of service

### Implementation Timeline

**Week 1-2**: Database models, invoice generation, basic UI
**Week 3**: Incoming payment tracking and reconciliation
**Week 4**: Outgoing payment workflow (SEPA batch generation)
**Week 5**: PayPal integration and testing
**Week 6**: Financial reporting, security audit, production deployment

---

## Future Enhancements (Post-MVP)

---

[← Back to Roadmap](README.md)
