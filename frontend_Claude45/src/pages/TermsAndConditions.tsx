/**
 * Terms and Conditions Page
 * Legal terms for using EasyAirClaim services
 */

export function TermsAndConditions() {
  return (
    <div className="py-12 bg-background">
      <div className="container max-w-4xl">
        <h1 className="text-4xl font-bold mb-2">Terms and Conditions</h1>
        <p className="text-muted-foreground mb-8">
          Last Updated: December 30, 2025
        </p>

        <div className="prose prose-slate dark:prose-invert max-w-none">
          {/* Introduction */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
            <p className="mb-4">
              Welcome to EasyAirClaim LLC ("Company," "we," "our," or "us"). These Terms and Conditions
              ("Terms") govern your use of our website and services located at www.easyairclaim.com
              (the "Service") and constitute a legally binding agreement between you ("Customer," "you,"
              or "your") and EasyAirClaim LLC, a limited liability company organized under the laws of
              the State of Florida, United States of America.
            </p>
            <p className="mb-4">
              By accessing or using our Service, you acknowledge that you have read, understood, and
              agree to be bound by these Terms. If you do not agree to these Terms, you must not use
              our Service.
            </p>
          </section>

          {/* Services Provided */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Services Provided</h2>
            <p className="mb-4">
              EasyAirClaim provides claim management services for flight compensation under EU Regulation
              261/2004 and other applicable air passenger rights regulations. Our services include:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Eligibility assessment for flight compensation claims</li>
              <li>Preparation and submission of compensation claims to airlines</li>
              <li>Communication and negotiation with airlines on your behalf</li>
              <li>Collection of compensation payments from airlines</li>
              <li>Transfer of compensation (minus our commission) to you</li>
            </ul>
            <p className="mb-4">
              <strong>Important Notice:</strong> EasyAirClaim does not provide legal advice or legal services.
              We act as your authorized representative in pursuing flight compensation claims with airlines.
              We do not guarantee any specific outcome or compensation amount, as final decisions are made by airlines.
            </p>
          </section>

          {/* Service Agreement */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. Service Agreement and Authorization</h2>

            <h3 className="text-xl font-semibold mb-3">3.1 Authorization to Act</h3>
            <p className="mb-4">
              By submitting a claim through our Service, you authorize EasyAirClaim LLC to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Act as your authorized representative for the submitted claim</li>
              <li>Communicate with airlines and relevant authorities on your behalf</li>
              <li>Receive compensation payments from airlines in your name</li>
              <li>Pursue claim resolution through appropriate channels if necessary and commercially viable</li>
              <li>Retain our commission from any recovered compensation before transferring the balance to you</li>
            </ul>

            <h4 className="text-lg font-semibold mb-3 mt-6">Power of Attorney Requirement</h4>
            <p className="mb-4">
              Upon submission of your claim, you agree to execute a Power of Attorney (PoA) in the form
              provided by us, which is incorporated herein by reference. This digital PoA document will be
              provided to you via email or through our secure customer portal and must be signed electronically
              to proceed with your claim.
            </p>
            <p className="mb-4">
              The Power of Attorney grants EasyAirClaim LLC the following specific powers:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Legal Representation:</strong> Authority to represent you before airlines, aviation authorities,
              dispute resolution bodies, and other third parties in connection with your claim</li>
              <li><strong>Claim Submission:</strong> Power to submit, file, and prosecute claims for flight compensation
              on your behalf under EU Regulation 261/2004 and other applicable regulations</li>
              <li><strong>Payment Receipt:</strong> Authorization to receive compensation payments from airlines directly
              in your name and on your behalf</li>
              <li><strong>Document Execution:</strong> Authority to sign documents, submit forms, and execute agreements
              necessary for the pursuit of your claim</li>
              <li><strong>Settlement Negotiation:</strong> Power to negotiate settlement terms with airlines, subject to
              your final approval for settlements below the statutory compensation amount</li>
              <li><strong>Information Access:</strong> Right to access and obtain all information from airlines and
              authorities related to your flight and claim</li>
            </ul>
            <p className="mb-4">
              <strong>Important Notes:</strong>
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>The Power of Attorney is limited in scope to the specific claim(s) you submit through our Service</li>
              <li>The PoA remains valid for the duration of your claim processing, including any appeals or dispute
              resolution proceedings</li>
              <li>You may revoke the Power of Attorney at any time by following the termination procedure outlined
              in Section 3.5</li>
              <li>A copy of the signed PoA will be stored securely in your account and is available for download at
              any time through the customer portal</li>
              <li>The Power of Attorney does not grant us authority over matters unrelated to your flight compensation claim</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">3.2 Client Obligations</h3>
            <p className="mb-4">
              You agree to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Provide accurate, complete, and truthful information about your flight and incident</li>
              <li>Upload genuine and unaltered supporting documents (boarding passes, receipts, etc.)</li>
              <li>Respond promptly to our requests for additional information or documentation</li>
              <li>Not pursue the same claim independently or through another service provider simultaneously</li>
              <li>Notify us immediately if you receive direct contact from the airline regarding your claim</li>
              <li>Not accept any settlement offer from the airline without our prior written consent</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">3.3 Our Obligations</h3>
            <p className="mb-4">
              EasyAirClaim LLC commits to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Provide you with regular updates on the progress of your claim</li>
              <li>Send you a status update at least once every 8 weeks regarding your claim's progress</li>
              <li>Act in good faith and with reasonable care in pursuing your claim</li>
              <li>Keep you informed of any significant developments, airline responses, or required actions</li>
              <li>Maintain the confidentiality and security of your personal information</li>
              <li>Process and transfer your compensation payment within 5-7 business days of receiving it from the airline</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">3.4 Exclusivity Period</h3>
            <p className="mb-4">
              Once you submit a claim through our Service, you grant us exclusive rights to pursue that
              specific claim for a period of 90 days from submission. You may not withdraw the claim or
              pursue it through other channels during this period without our written consent.
            </p>

            <h3 className="text-xl font-semibold mb-3">3.5 Termination of Claim or Agreement</h3>
            <p className="mb-4">
              You have the right to terminate this agreement and withdraw your claim at any time by sending
              a written notice to support@easyairclaim.com. To ensure proper processing, please use the
              following template:
            </p>
            <div className="bg-muted p-6 rounded-lg mb-4 font-mono text-sm">
              <p className="mb-2">Subject: Claim Termination Request - [Your Claim ID]</p>
              <p className="mb-4">Dear EasyAirClaim Support Team,</p>
              <p className="mb-2">I hereby formally request the termination of my claim agreement and withdrawal of my claim with the following details:</p>
              <p className="mb-1 ml-4">- Full Name: [Your Full Name]</p>
              <p className="mb-1 ml-4">- Email Address: [Your Email]</p>
              <p className="mb-1 ml-4">- Claim ID: [Your Claim ID]</p>
              <p className="mb-1 ml-4">- Flight Number: [Flight Number]</p>
              <p className="mb-1 ml-4">- Flight Date: [Flight Date]</p>
              <p className="mb-4 ml-4">- Reason for Termination: [Optional - Brief Explanation]</p>
              <p className="mb-2">I understand that:</p>
              <p className="mb-1 ml-4">1. This termination will take effect within 5 business days of receipt</p>
              <p className="mb-1 ml-4">2. If compensation has already been received, applicable fees will still apply</p>
              <p className="mb-1 ml-4">3. I may pursue this claim independently or through other services after termination</p>
              <p className="mb-4">Sincerely,</p>
              <p>[Your Full Name]</p>
              <p>[Date]</p>
            </div>
            <p className="mb-4">
              <strong>Important Notes:</strong>
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Termination requests will be processed within 5 business days of receipt</li>
              <li>If we have already received compensation from the airline before termination, our commission (20% + VAT) will still apply to the amount recovered</li>
              <li>After termination, you are free to pursue the claim independently or through another service provider</li>
              <li>Any third-party costs already incurred on your behalf may be charged to you upon termination</li>
              <li>We will provide confirmation of termination via email within 5 business days</li>
            </ul>
          </section>

          {/* Fees and Payment */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Fees and Payment Terms</h2>

            <h3 className="text-xl font-semibold mb-3">4.1 No Win, No Fee</h3>
            <p className="mb-4">
              We operate on a "no win, no fee" basis. You pay nothing if we do not successfully recover
              compensation for you. Our fee is only charged if and when compensation is successfully obtained.
            </p>

            <h3 className="text-xl font-semibold mb-3">4.2 Commission Structure</h3>
            <p className="mb-4">
              Our standard commission is <strong>20% (twenty percent) of the gross compensation amount
              recovered</strong>, plus applicable taxes (VAT/sales tax). This commission covers all our
              services, including:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Claim assessment and preparation</li>
              <li>Communication and negotiation with airlines</li>
              <li>Representation and advocacy services</li>
              <li>Payment collection and transfer</li>
              <li>Administrative and operational costs</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">4.3 Payment Process</h3>
            <p className="mb-4">
              When an airline pays compensation:
            </p>
            <ol className="list-decimal pl-6 mb-4 space-y-2">
              <li>The airline transfers the full compensation amount to EasyAirClaim LLC</li>
              <li>We deduct our 20% commission plus applicable taxes</li>
              <li>We transfer the remaining balance to your designated bank account within 5-7 business days</li>
              <li>You receive a detailed breakdown of the payment calculation</li>
            </ol>

            <h3 className="text-xl font-semibold mb-3">4.4 Third-Party Costs</h3>
            <p className="mb-4">
              In exceptional cases where external proceedings or professional services are required, we reserve
              the right to request your consent before incurring additional third-party costs (filing fees,
              expert consultants, etc.). Such costs, if approved by you, may be deducted from the compensation
              or billed separately.
            </p>

            <h3 className="text-xl font-semibold mb-3">4.5 Currency and Taxes</h3>
            <p className="mb-4">
              Compensation amounts are typically paid in Euros (EUR) as specified under EU261/2004. Currency
              conversion fees, if applicable, will be disclosed before payment. You are responsible for any
              taxes on compensation received in your jurisdiction.
            </p>
          </section>

          {/* User Accounts and Security */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. User Accounts and Security</h2>

            <h3 className="text-xl font-semibold mb-3">5.1 Account Creation</h3>
            <p className="mb-4">
              You may access our Service using passwordless authentication (magic link) sent to your email
              address. By creating an account, you represent that:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>You are at least 18 years of age or the age of majority in your jurisdiction</li>
              <li>You have the legal capacity to enter into binding contracts</li>
              <li>The information you provide is accurate and current</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">5.2 Account Security</h3>
            <p className="mb-4">
              You are responsible for:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Maintaining the confidentiality of your account access</li>
              <li>All activities that occur under your account</li>
              <li>Notifying us immediately of any unauthorized use</li>
              <li>Ensuring your email account is secure (as it's used for authentication)</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">5.3 Account Termination</h3>
            <p className="mb-4">
              We reserve the right to suspend or terminate your account if:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>You violate these Terms</li>
              <li>You provide false or misleading information</li>
              <li>You engage in fraudulent or illegal activities</li>
              <li>Your account is inactive for more than 2 years (with 30 days prior notice)</li>
            </ul>
          </section>

          {/* Intellectual Property */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Intellectual Property Rights</h2>
            <p className="mb-4">
              All content on our Service, including but not limited to text, graphics, logos, software,
              and user interfaces, is the property of EasyAirClaim LLC or its licensors and is protected
              by United States and international copyright, trademark, and other intellectual property laws.
            </p>
            <p className="mb-4">
              You may not:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Copy, modify, distribute, or reverse engineer any part of our Service</li>
              <li>Use our branding, logos, or trademarks without written permission</li>
              <li>Create derivative works based on our Service</li>
              <li>Remove or alter any copyright, trademark, or proprietary notices</li>
            </ul>
          </section>

          {/* Privacy and Data Protection */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Privacy and Data Protection</h2>
            <p className="mb-4">
              Your privacy is important to us. Our collection, use, and protection of your personal data
              is governed by our Privacy Policy, which is incorporated into these Terms by reference.
              By using our Service, you consent to our data practices as described in the Privacy Policy.
            </p>
            <p className="mb-4">
              We comply with applicable data protection laws, including the General Data Protection
              Regulation (GDPR) for European customers and relevant Florida and U.S. federal privacy laws.
            </p>
          </section>

          {/* Disclaimers and Limitations */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Disclaimers and Limitations of Liability</h2>

            <h3 className="text-xl font-semibold mb-3">8.1 Service Availability</h3>
            <p className="mb-4">
              Our Service is provided "as is" and "as available." We do not guarantee that:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>The Service will be uninterrupted, timely, secure, or error-free</li>
              <li>Any errors or defects will be corrected</li>
              <li>The Service will meet your specific requirements</li>
              <li>Any claim will result in successful compensation</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">8.2 No Guarantee of Outcome</h3>
            <p className="mb-4">
              While we use our best efforts to pursue your claim, we cannot guarantee:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>That compensation will be awarded by the airline</li>
              <li>The amount of compensation if awarded</li>
              <li>The time required to resolve your claim</li>
              <li>Success in resolving your claim through available channels</li>
            </ul>
            <p className="mb-4">
              Airlines may refuse compensation based on extraordinary circumstances or other defenses.
              The final determination of eligibility and compensation amount rests with the airline or
              relevant dispute resolution authorities.
            </p>

            <h3 className="text-xl font-semibold mb-3">8.3 Limitation of Liability</h3>
            <p className="mb-4">
              TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, EASYAIRCLAIM LLC SHALL NOT BE LIABLE FOR:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Any indirect, incidental, special, consequential, or punitive damages</li>
              <li>Loss of profits, revenue, data, or business opportunities</li>
              <li>Damages resulting from your inability to use the Service</li>
              <li>Damages arising from errors, mistakes, or inaccuracies in content</li>
              <li>Unauthorized access to or alteration of your data</li>
            </ul>
            <p className="mb-4">
              Our total liability to you for any claim arising from or relating to these Terms or the
              Service shall not exceed the amount of fees paid by you to us in the 12 months preceding
              the claim, or $100 USD, whichever is greater.
            </p>

            <h3 className="text-xl font-semibold mb-3">8.4 Force Majeure</h3>
            <p className="mb-4">
              We shall not be liable for any failure or delay in performance due to circumstances beyond
              our reasonable control, including but not limited to acts of God, natural disasters, war,
              terrorism, labor disputes, government actions, pandemics, or failures of third-party services.
            </p>
          </section>

          {/* Indemnification */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Indemnification</h2>
            <p className="mb-4">
              You agree to indemnify, defend, and hold harmless EasyAirClaim LLC, its officers, directors,
              employees, agents, and affiliates from and against any claims, liabilities, damages, losses,
              costs, or expenses (including reasonable professional fees) arising from:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Your violation of these Terms</li>
              <li>Your violation of any applicable law or regulation</li>
              <li>Your submission of false, misleading, or fraudulent information</li>
              <li>Your infringement of any third-party rights</li>
              <li>Your misuse of the Service</li>
            </ul>
          </section>

          {/* Governing Law and Dispute Resolution */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Governing Law and Dispute Resolution</h2>

            <h3 className="text-xl font-semibold mb-3">10.1 Governing Law</h3>
            <p className="mb-4">
              These Terms shall be governed by and construed in accordance with the laws of the State of
              Florida, United States of America, without regard to its conflict of law provisions.
            </p>
            <p className="mb-4">
              Alternatively, both parties may agree to resolve disputes through a neutral arbitration body
              such as the American Arbitration Association (AAA) under its Consumer Arbitration Rules. Either
              party may propose arbitration by providing written notice to the other party.
            </p>

            <h3 className="text-xl font-semibold mb-3">10.2 Jurisdiction and Venue</h3>
            <p className="mb-4">
              Any formal action or proceeding arising out of or relating to these Terms or the Service shall
              be brought exclusively in the state or federal courts located in Florida, and you hereby
              consent to the personal jurisdiction and venue of such courts.
            </p>

            <h3 className="text-xl font-semibold mb-3">10.3 Informal Dispute Resolution</h3>
            <p className="mb-4">
              Before filing any formal action, you agree to first contact us at support@easyairclaim.com
              and attempt to resolve the dispute informally through good-faith negotiations for at least 30 days.
            </p>

            <h3 className="text-xl font-semibold mb-3">10.4 Class Action Waiver</h3>
            <p className="mb-4">
              You agree that any dispute resolution proceedings will be conducted only on an individual
              basis and not in a class, consolidated, or representative action. You waive any right to
              participate in a class action lawsuit or class-wide arbitration.
            </p>
          </section>

          {/* Changes to Terms */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Modifications to Terms</h2>
            <p className="mb-4">
              We reserve the right to modify these Terms at any time. When we make material changes, we will:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Update the "Last Updated" date at the top of this page</li>
              <li>Notify you via email or through a prominent notice on our Service</li>
              <li>Provide at least 30 days' notice before changes take effect</li>
            </ul>
            <p className="mb-4">
              Your continued use of the Service after changes become effective constitutes your acceptance
              of the revised Terms. If you do not agree to the changes, you must stop using the Service.
            </p>
            <p className="mb-4">
              <strong>Important:</strong> Changes to Terms do not affect claims submitted before the change
              date. Such claims remain governed by the Terms in effect at the time of submission.
            </p>
          </section>

          {/* General Provisions */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. General Provisions</h2>

            <h3 className="text-xl font-semibold mb-3">12.1 Entire Agreement</h3>
            <p className="mb-4">
              These Terms, together with our Privacy Policy and any other legal notices published on the
              Service, constitute the entire agreement between you and EasyAirClaim LLC regarding the Service.
            </p>

            <h3 className="text-xl font-semibold mb-3">12.2 Severability</h3>
            <p className="mb-4">
              If any provision of these Terms is found to be invalid or unenforceable, that provision shall
              be limited or eliminated to the minimum extent necessary, and the remaining provisions shall
              remain in full force and effect.
            </p>

            <h3 className="text-xl font-semibold mb-3">12.3 Waiver</h3>
            <p className="mb-4">
              Our failure to enforce any right or provision of these Terms shall not constitute a waiver of
              such right or provision. Any waiver must be in writing and signed by an authorized representative
              of EasyAirClaim LLC.
            </p>

            <h3 className="text-xl font-semibold mb-3">12.4 Assignment</h3>
            <p className="mb-4">
              You may not assign or transfer these Terms or your rights hereunder without our prior written
              consent. We may assign these Terms or any rights hereunder without restriction.
            </p>

            <h3 className="text-xl font-semibold mb-3">12.5 Notices</h3>
            <p className="mb-4">
              All notices to you will be sent to the email address you provide during registration. Notices
              to us should be sent to:
            </p>
            <div className="bg-muted p-4 rounded-lg mb-4">
              <p className="font-semibold">EasyAirClaim LLC</p>
              <p>Legal Department</p>
              <p>Email: legal@easyairclaim.com</p>
              <p>Address: [Florida Business Address]</p>
            </div>

            <h3 className="text-xl font-semibold mb-3">12.6 Survival</h3>
            <p className="mb-4">
              Provisions that by their nature should survive termination shall survive, including but not
              limited to: ownership provisions, warranty disclaimers, indemnification, limitations of liability,
              and dispute resolution provisions.
            </p>

            <h3 className="text-xl font-semibold mb-3">12.7 Language</h3>
            <p className="mb-4">
              These Terms are drafted in English. Any translations are provided for convenience only. In case
              of conflict between the English version and any translation, the English version shall prevail.
            </p>
          </section>

          {/* Contact Information */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">13. Contact Information</h2>
            <p className="mb-4">
              If you have any questions about these Terms, please contact us:
            </p>
            <div className="bg-muted p-6 rounded-lg">
              <p className="font-semibold text-lg mb-2">EasyAirClaim LLC</p>
              <p className="mb-1">Email: support@easyairclaim.com</p>
              <p className="mb-1">Legal: legal@easyairclaim.com</p>
              <p className="mb-1">Phone: [Phone Number]</p>
              <p className="mb-1">Business Address: [Florida Address]</p>
              <p className="mb-1">Hours: Monday-Friday, 9:00 AM - 5:00 PM EST</p>
            </div>
          </section>

          {/* Acceptance */}
          <section className="mb-8">
            <div className="bg-primary/10 border-l-4 border-primary p-6 rounded">
              <h2 className="text-xl font-semibold mb-3">Acceptance of Terms</h2>
              <p className="mb-2">
                BY CLICKING "I AGREE," CHECKING THE ACCEPTANCE BOX, SUBMITTING A CLAIM, OR OTHERWISE
                ACCESSING OR USING THE SERVICE, YOU ACKNOWLEDGE THAT YOU HAVE READ, UNDERSTOOD, AND
                AGREE TO BE BOUND BY THESE TERMS AND CONDITIONS.
              </p>
              <p className="text-sm text-muted-foreground mt-4">
                If you do not agree to these Terms, you must not use our Service.
              </p>
            </div>
          </section>
        </div>

        {/* Back to Home */}
        <div className="mt-12 text-center">
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-6 py-2"
          >
            Back to Home
          </a>
        </div>
      </div>
    </div>
  );
}
