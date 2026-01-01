/**
 * Privacy Policy Page
 * Details on data collection, usage, and protection
 */

export function PrivacyPolicy() {
  return (
    <div className="py-12 bg-background">
      <div className="container max-w-4xl">
        <h1 className="text-4xl font-bold mb-2">Privacy Policy</h1>
        <p className="text-muted-foreground mb-8">
          Last Updated: January 1, 2026
        </p>

        <div className="prose prose-slate dark:prose-invert max-w-none">
          {/* Introduction */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
            <p className="mb-4">
              EasyAirClaim LLC ("we," "our," or "us") is committed to protecting your privacy and ensuring the
              security of your personal information. This Privacy Policy explains how we collect, use, disclose,
              and safeguard your information when you use our website and services located at www.easyairclaim.com
              (the "Service").
            </p>
            <p className="mb-4">
              By using our Service, you consent to the data practices described in this policy. If you do not
              agree with the terms of this Privacy Policy, please do not access or use the Service.
            </p>
            <p className="mb-4">
              <strong>Important:</strong> We comply with the General Data Protection Regulation (GDPR), the
              California Consumer Privacy Act (CCPA), and other applicable data protection laws.
            </p>
          </section>

          {/* Information We Collect */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Information We Collect</h2>

            <h3 className="text-xl font-semibold mb-3">2.1 Personal Information You Provide</h3>
            <p className="mb-4">
              When you use our Service, we collect the following personal information that you voluntarily provide:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Account Information:</strong> Name, email address, phone number, and password</li>
              <li><strong>Flight Information:</strong> Flight number, departure/arrival airports, flight dates, booking reference</li>
              <li><strong>Identification Documents:</strong> Passport, national ID card, or driver's license (for claim verification)</li>
              <li><strong>Travel Documents:</strong> Boarding passes, flight tickets, receipts</li>
              <li><strong>Banking Information:</strong> Bank account details (IBAN/SWIFT) for compensation payments</li>
              <li><strong>Address Information:</strong> Street address, city, postal code, country</li>
              <li><strong>Communication Data:</strong> Messages, emails, and other correspondence with our support team</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">2.2 Information Automatically Collected</h3>
            <p className="mb-4">
              When you access our Service, we automatically collect certain information:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Usage Data:</strong> Pages visited, time spent on pages, links clicked, navigation paths</li>
              <li><strong>Device Information:</strong> IP address, browser type and version, operating system, device type</li>
              <li><strong>Location Data:</strong> Approximate geographic location based on IP address</li>
              <li><strong>Cookies and Tracking:</strong> Session cookies, authentication tokens, preference settings</li>
              <li><strong>Log Data:</strong> Access times, error logs, performance metrics</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">2.3 Information from Third Parties</h3>
            <p className="mb-4">
              We may receive information from:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Airlines:</strong> Flight status, delay/cancellation information, passenger manifest data</li>
              <li><strong>Aviation Databases:</strong> Flight tracking data, airport information, weather conditions</li>
              <li><strong>Payment Processors:</strong> Transaction confirmations, payment status</li>
            </ul>
          </section>

          {/* How We Use Your Information */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Information</h2>
            <p className="mb-4">
              We use your personal information for the following purposes:
            </p>

            <h3 className="text-xl font-semibold mb-3">3.1 Service Delivery</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Processing and managing your flight compensation claims</li>
              <li>Verifying your eligibility for compensation under EU261/2004</li>
              <li>Communicating with airlines on your behalf</li>
              <li>Transferring compensation payments to your bank account</li>
              <li>Providing customer support and responding to inquiries</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">3.2 Legal and Compliance</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Complying with legal obligations and regulations</li>
              <li>Preventing fraud, unauthorized access, and illegal activities</li>
              <li>Enforcing our Terms and Conditions</li>
              <li>Responding to legal requests from authorities</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">3.3 Service Improvement</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Analyzing usage patterns to improve our Service</li>
              <li>Conducting research and development</li>
              <li>Personalizing your user experience</li>
              <li>Monitoring and improving security measures</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">3.4 Communication</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Sending claim status updates and notifications</li>
              <li>Providing important service announcements</li>
              <li>Sending marketing communications (with your consent)</li>
              <li>Requesting feedback and reviews</li>
            </ul>
          </section>

          {/* Data Security */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Data Security and Protection</h2>

            <h3 className="text-xl font-semibold mb-3">4.1 Security Measures</h3>
            <p className="mb-4">
              We implement industry-standard security measures to protect your personal information:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Encryption:</strong> All uploaded files are encrypted using Fernet encryption before storage</li>
              <li><strong>SSL/TLS:</strong> 256-bit SSL encryption for all data transmission</li>
              <li><strong>Access Controls:</strong> Role-based access control with authentication and authorization</li>
              <li><strong>Secure Storage:</strong> Documents stored on encrypted Nextcloud servers</li>
              <li><strong>Password Security:</strong> Passwords hashed using bcrypt algorithm</li>
              <li><strong>Regular Audits:</strong> Periodic security assessments and vulnerability testing</li>
              <li><strong>Data Minimization:</strong> We only collect data necessary for providing our services</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">4.2 Data Retention</h3>
            <p className="mb-4">
              We retain your personal information only as long as necessary:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Active Claims:</strong> For the duration of claim processing and resolution</li>
              <li><strong>Completed Claims:</strong> 7 years after claim closure (for legal and tax compliance)</li>
              <li><strong>Account Data:</strong> Until you request deletion or account closure</li>
              <li><strong>Marketing Data:</strong> Until you withdraw consent or request deletion</li>
              <li><strong>Legal Requirements:</strong> As required by applicable laws and regulations</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">4.3 Data Breach Notification</h3>
            <p className="mb-4">
              In the event of a data breach that affects your personal information, we will:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Notify you within 72 hours of becoming aware of the breach</li>
              <li>Inform relevant supervisory authorities as required by law</li>
              <li>Provide details about the nature and scope of the breach</li>
              <li>Describe the measures taken to address the breach</li>
              <li>Offer recommendations to protect your information</li>
            </ul>
          </section>

          {/* Data Sharing */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Data Sharing and Disclosure</h2>

            <h3 className="text-xl font-semibold mb-3">5.1 We Share Information With:</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Airlines:</strong> To submit and pursue your compensation claims</li>
              <li><strong>Payment Processors:</strong> To transfer compensation payments to your bank account</li>
              <li><strong>Cloud Service Providers:</strong> For secure file storage (Nextcloud) and database hosting</li>
              <li><strong>Email Service Providers:</strong> For sending claim updates and notifications</li>
              <li><strong>Legal Authorities:</strong> When required by law or to protect our legal rights</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">5.2 We Do NOT:</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Sell your personal information to third parties</li>
              <li>Share your data for third-party marketing purposes</li>
              <li>Disclose your information without legal basis or your consent</li>
              <li>Transfer data to countries without adequate data protection</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">5.3 International Data Transfers</h3>
            <p className="mb-4">
              Your information may be transferred to and processed in the United States. We ensure appropriate
              safeguards are in place through:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Standard Contractual Clauses (SCCs) approved by the European Commission</li>
              <li>Adequacy decisions where applicable</li>
              <li>Your explicit consent for specific transfers</li>
            </ul>
          </section>

          {/* Your Rights */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Your Privacy Rights</h2>

            <h3 className="text-xl font-semibold mb-3">6.1 GDPR Rights (European Users)</h3>
            <p className="mb-4">
              If you are located in the European Economic Area (EEA), you have the following rights:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Right of Access:</strong> Request a copy of your personal information</li>
              <li><strong>Right to Rectification:</strong> Correct inaccurate or incomplete data</li>
              <li><strong>Right to Erasure:</strong> Request deletion of your personal information ("right to be forgotten")</li>
              <li><strong>Right to Restriction:</strong> Limit how we use your data</li>
              <li><strong>Right to Data Portability:</strong> Receive your data in a structured, machine-readable format</li>
              <li><strong>Right to Object:</strong> Object to processing of your personal information</li>
              <li><strong>Right to Withdraw Consent:</strong> Withdraw consent at any time</li>
              <li><strong>Right to Lodge a Complaint:</strong> File a complaint with your data protection authority</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">6.2 CCPA Rights (California Users)</h3>
            <p className="mb-4">
              If you are a California resident, you have the following rights:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Right to Know:</strong> Request disclosure of data collection and sharing practices</li>
              <li><strong>Right to Delete:</strong> Request deletion of your personal information</li>
              <li><strong>Right to Opt-Out:</strong> Opt-out of the sale of personal information (we do not sell data)</li>
              <li><strong>Right to Non-Discrimination:</strong> Equal service regardless of privacy rights exercise</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">6.3 How to Exercise Your Rights</h3>
            <p className="mb-4">
              To exercise any of your privacy rights, contact us at:
            </p>
            <div className="bg-muted p-4 rounded-lg mb-4">
              <p className="font-semibold">Privacy Rights Requests</p>
              <p>Email: privacy@easyairclaim.com</p>
              <p>Subject: Privacy Rights Request - [Your Name]</p>
              <p className="mt-2 text-sm text-muted-foreground">
                We will respond to your request within 30 days (or 45 days if complex).
              </p>
            </div>
          </section>

          {/* Cookies */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Cookies and Tracking Technologies</h2>

            <h3 className="text-xl font-semibold mb-3">7.1 What We Use</h3>
            <p className="mb-4">
              We use the following types of cookies and tracking technologies:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Essential Cookies:</strong> Required for authentication, security, and basic functionality</li>
              <li><strong>Preference Cookies:</strong> Remember your settings (language, dark mode, etc.)</li>
              <li><strong>Analytics Cookies:</strong> Understand how users interact with our Service</li>
              <li><strong>Session Cookies:</strong> Maintain your login state and session data</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3">7.2 Your Choices</h3>
            <p className="mb-4">
              You can control cookies through:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Browser settings to block or delete cookies</li>
              <li>Opt-out links for third-party analytics services</li>
              <li>Cookie consent banner preferences</li>
            </ul>
            <p className="mb-4">
              Note: Blocking essential cookies may affect Service functionality.
            </p>
          </section>

          {/* Children's Privacy */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Children's Privacy</h2>
            <p className="mb-4">
              Our Service is not intended for individuals under the age of 18. We do not knowingly collect
              personal information from children. If you are a parent or guardian and believe your child has
              provided us with personal information, please contact us immediately at privacy@easyairclaim.com.
            </p>
            <p className="mb-4">
              If we become aware that we have collected personal information from a child under 18 without
              parental consent, we will take steps to delete that information as quickly as possible.
            </p>
          </section>

          {/* Third-Party Links */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Third-Party Websites and Services</h2>
            <p className="mb-4">
              Our Service may contain links to third-party websites, services, or resources. We are not
              responsible for the privacy practices or content of these external sites. We encourage you to
              review the privacy policies of any third-party services you access.
            </p>
            <p className="mb-4">
              Third-party services we integrate with include:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Payment processors for fund transfers</li>
              <li>Cloud storage providers for document management</li>
              <li>Email service providers for communications</li>
              <li>Analytics services for usage tracking</li>
            </ul>
          </section>

          {/* Changes to Policy */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Changes to This Privacy Policy</h2>
            <p className="mb-4">
              We may update this Privacy Policy from time to time to reflect changes in our practices,
              technology, legal requirements, or other factors. When we make material changes, we will:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Update the "Last Updated" date at the top of this page</li>
              <li>Notify you via email or through a prominent notice on our Service</li>
              <li>Provide at least 30 days' notice before changes take effect</li>
              <li>Request your consent if required by applicable law</li>
            </ul>
            <p className="mb-4">
              Your continued use of the Service after changes become effective constitutes acceptance of
              the updated Privacy Policy. We encourage you to review this policy periodically.
            </p>
          </section>

          {/* Legal Basis */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Legal Basis for Processing (GDPR)</h2>
            <p className="mb-4">
              Under GDPR, we process your personal information based on the following legal grounds:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Contract Performance:</strong> Processing necessary to provide our services and fulfill our contractual obligations</li>
              <li><strong>Consent:</strong> You have given explicit consent for specific processing activities</li>
              <li><strong>Legitimate Interests:</strong> Processing necessary for our legitimate business interests (fraud prevention, service improvement)</li>
              <li><strong>Legal Obligation:</strong> Processing required to comply with legal and regulatory requirements</li>
              <li><strong>Vital Interests:</strong> Processing necessary to protect your vital interests or those of others</li>
            </ul>
          </section>

          {/* Contact Information */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. Contact Us</h2>
            <p className="mb-4">
              If you have questions, concerns, or requests regarding this Privacy Policy or our data practices,
              please contact us:
            </p>
            <div className="bg-muted p-6 rounded-lg">
              <p className="font-semibold text-lg mb-2">EasyAirClaim LLC - Privacy Officer</p>
              <p className="mb-1">Email: privacy@easyairclaim.com</p>
              <p className="mb-1">Support: support@easyairclaim.com</p>
              <p className="mb-1">Legal: legal@easyairclaim.com</p>
              <p className="mb-1">Address: 3436 SW 8th Pl, Cape Coral 33914</p>
              <p className="mb-1">Phone: [Phone Number]</p>
              <p className="mb-3">Hours: Monday-Friday, 9:00 AM - 5:00 PM EST</p>

              <div className="mt-4 pt-4 border-t">
                <p className="font-semibold mb-2">Data Protection Officer (DPO)</p>
                <p className="mb-1">Email: dpo@easyairclaim.com</p>
                <p className="text-sm text-muted-foreground">
                  For GDPR-related inquiries and data protection matters
                </p>
              </div>
            </div>
          </section>

          {/* Supervisory Authority */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">13. Supervisory Authority</h2>
            <p className="mb-4">
              If you are located in the EEA and have concerns about our data processing practices that we
              have not adequately addressed, you have the right to lodge a complaint with your local data
              protection supervisory authority.
            </p>
            <p className="mb-4">
              You can find your supervisory authority contact information at:{' '}
              <a
                href="https://edpb.europa.eu/about-edpb/about-edpb/members_en"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                European Data Protection Board
              </a>
            </p>
          </section>

          {/* Acknowledgment */}
          <section className="mb-8">
            <div className="bg-primary/10 border-l-4 border-primary p-6 rounded">
              <h2 className="text-xl font-semibold mb-3">Acknowledgment and Consent</h2>
              <p className="mb-2">
                BY USING OUR SERVICE, YOU ACKNOWLEDGE THAT YOU HAVE READ AND UNDERSTOOD THIS PRIVACY POLICY
                AND AGREE TO THE COLLECTION, USE, AND DISCLOSURE OF YOUR PERSONAL INFORMATION AS DESCRIBED HEREIN.
              </p>
              <p className="text-sm text-muted-foreground mt-4">
                If you do not agree with this Privacy Policy, please do not use our Service.
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
