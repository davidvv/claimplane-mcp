"""
Browser E2E test for draft resume UX fix (WP 196)

Tests the complete flow of:
1. Accessing /claim/new?resume=<draft_id> while logged out
2. Being redirected to /auth with "Welcome back!" banner
3. Completing magic link authentication
4. Being redirected back to /claim/new?resume=<draft_id> (NOT /my-claims)
5. Draft data being loaded correctly
"""
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import psycopg2


class DraftResumeTest:
    """E2E test for draft resume functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.draft_id = "5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f"
        self.test_email = "florian.luhn@outlook.com"
        self.screenshots_dir = "/home/david/claimplane/claimplane/tests/e2e/screenshots"
        self.console_logs = []
        self.errors = []
        
        # Database connection for fetching magic link token
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'easyair_db',
            'user': 'easyair_user',
            'password': 'easyair_password'
        }
        
        # Create screenshots directory
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def capture_console(self, msg):
        """Capture console messages from the browser"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': msg.type,
            'text': msg.text
        }
        self.console_logs.append(log_entry)
        print(f"[CONSOLE {msg.type.upper()}] {msg.text}")
    
    def capture_error(self, error):
        """Capture page errors"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error)
        }
        self.errors.append(error_entry)
        print(f"[PAGE ERROR] {error}")
    
    async def get_magic_link_token(self) -> str:
        """Fetch the most recent magic link token from database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = """
                SELECT token FROM magic_link_tokens 
                WHERE email = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            cursor.execute(query, (self.test_email,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return result[0]
            else:
                raise Exception(f"No magic link token found for {self.test_email}")
        except Exception as e:
            raise Exception(f"Failed to fetch magic link token: {str(e)}")
    
    async def check_session_storage(self, page: Page, key: str) -> str:
        """Check sessionStorage for a specific key"""
        value = await page.evaluate(f"""() => {{
            return sessionStorage.getItem('{key}');
        }}""")
        return value
    
    async def run_test(self):
        """Execute the complete test flow"""
        print("\n" + "="*80)
        print("DRAFT RESUME UX TEST - WP 196")
        print("="*80 + "\n")
        
        async with async_playwright() as p:
            # Launch browser with visible UI for debugging
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            # Setup console and error listeners
            page.on("console", self.capture_console)
            page.on("pageerror", self.capture_error)
            
            try:
                # Step 1: Navigate to homepage and clear storage
                print("Step 1: Opening homepage and clearing storage...")
                await page.goto(self.base_url)
                await page.evaluate("() => { sessionStorage.clear(); localStorage.clear(); }")
                
                # Clear cookies
                await context.clear_cookies()
                print("✓ Storage cleared\n")
                
                # Step 2: Navigate to draft resume URL
                resume_url = f"{self.base_url}/claim/new?resume={self.draft_id}"
                print(f"Step 2: Navigating to draft resume URL...")
                print(f"  URL: {resume_url}")
                await page.goto(resume_url)
                await page.wait_for_load_state('networkidle')
                
                # Step 3: Verify redirect to /auth
                current_url = page.url
                print(f"\nStep 3: Checking redirect to /auth...")
                print(f"  Current URL: {current_url}")
                
                if '/auth' not in current_url:
                    self.errors.append({
                        'step': 'redirect_check',
                        'expected': 'URL should contain /auth',
                        'actual': current_url
                    })
                    print("✗ FAILED: Not redirected to /auth page")
                else:
                    print("✓ Redirected to /auth page")
                
                # Step 4: Take screenshot and check for "Welcome back!" banner
                screenshot_path = f"{self.screenshots_dir}/01_auth_page.png"
                await page.screenshot(path=screenshot_path)
                print(f"\n✓ Screenshot saved: {screenshot_path}")
                
                # Check for banner
                try:
                    banner = await page.wait_for_selector('text=Welcome back!', timeout=5000)
                    if banner:
                        print("✓ 'Welcome back!' banner found")
                    else:
                        print("✗ 'Welcome back!' banner NOT found")
                        self.errors.append({'step': 'banner_check', 'error': 'Banner not found'})
                except Exception as e:
                    print(f"✗ 'Welcome back!' banner NOT found: {str(e)}")
                    self.errors.append({'step': 'banner_check', 'error': str(e)})
                
                # Step 5: Check sessionStorage for postLoginRedirect
                print("\nStep 5: Checking sessionStorage...")
                post_login_redirect = await self.check_session_storage(page, 'postLoginRedirect')
                expected_redirect = f'/claim/new?resume={self.draft_id}'
                
                print(f"  postLoginRedirect: {post_login_redirect}")
                print(f"  Expected: {expected_redirect}")
                
                if post_login_redirect == expected_redirect:
                    print("✓ sessionStorage contains correct redirect URL")
                else:
                    print("✗ FAILED: sessionStorage redirect mismatch")
                    self.errors.append({
                        'step': 'session_storage_check',
                        'expected': expected_redirect,
                        'actual': post_login_redirect
                    })
                
                # Step 6: Enter email and request magic link
                print(f"\nStep 6: Requesting magic link for {self.test_email}...")
                
                # Find and fill email input
                email_input = await page.wait_for_selector('input[type="email"]', timeout=5000)
                await email_input.fill(self.test_email)
                
                # Submit form
                submit_button = await page.wait_for_selector('button[type="submit"]', timeout=5000)
                await submit_button.click()
                
                # Wait for success message
                await page.wait_for_load_state('networkidle')
                print("✓ Magic link request submitted")
                
                # Step 7: Get magic link token from database
                print("\nStep 7: Fetching magic link token from database...")
                await asyncio.sleep(2)  # Give the server time to create the token
                
                try:
                    token = await self.get_magic_link_token()
                    print(f"✓ Token retrieved: {token[:20]}...")
                except Exception as e:
                    print(f"✗ FAILED to get token: {str(e)}")
                    self.errors.append({'step': 'token_fetch', 'error': str(e)})
                    await browser.close()
                    return False
                
                # Step 8: Navigate to magic link URL
                magic_link_url = f"{self.base_url}/auth/magic-link?token={token}"
                print(f"\nStep 8: Navigating to magic link URL...")
                print(f"  URL: {magic_link_url}")
                
                await page.goto(magic_link_url)
                
                # Step 9: Wait for verification and redirect
                print("\nStep 9: Waiting for verification and redirect...")
                await asyncio.sleep(3)  # Wait for verification process
                await page.wait_for_load_state('networkidle')
                
                # Step 10: CRITICAL CHECK - Verify final URL
                final_url = page.url
                print(f"\nStep 10: CRITICAL CHECK - Verifying final URL...")
                print(f"  Final URL: {final_url}")
                print(f"  Expected: {self.base_url}/claim/new?resume={self.draft_id}")
                
                test_passed = True
                
                if f'/claim/new?resume={self.draft_id}' in final_url:
                    print("✓✓✓ SUCCESS: Redirected to draft resume page!")
                elif '/my-claims' in final_url:
                    print("✗✗✗ FAILED: Redirected to /my-claims instead of draft resume!")
                    test_passed = False
                    self.errors.append({
                        'step': 'final_redirect',
                        'error': 'Redirected to /my-claims instead of draft resume',
                        'expected': f'/claim/new?resume={self.draft_id}',
                        'actual': final_url
                    })
                else:
                    print(f"✗✗✗ FAILED: Unexpected redirect destination: {final_url}")
                    test_passed = False
                    self.errors.append({
                        'step': 'final_redirect',
                        'error': 'Unexpected redirect destination',
                        'expected': f'/claim/new?resume={self.draft_id}',
                        'actual': final_url
                    })
                
                # Step 11: Take final screenshot
                screenshot_path = f"{self.screenshots_dir}/02_final_page.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"\n✓ Final screenshot saved: {screenshot_path}")
                
                # Step 12: Check if draft data is loaded
                print("\nStep 12: Checking if draft data is loaded...")
                await asyncio.sleep(2)
                
                # Take another screenshot after data loads
                screenshot_path = f"{self.screenshots_dir}/03_draft_loaded.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"✓ Draft loaded screenshot saved: {screenshot_path}")
                
                # Check console logs for key messages
                print("\n" + "="*80)
                print("CONSOLE LOG ANALYSIS")
                print("="*80)
                
                has_pending_redirect = any('Pending redirect from sessionStorage' in log['text'] for log in self.console_logs)
                has_resuming_flow = any('Resuming interrupted flow' in log['text'] for log in self.console_logs)
                has_my_claims_redirect = any('Redirecting to My Claims page' in log['text'] for log in self.console_logs)
                
                print(f"✓ Found 'Pending redirect from sessionStorage': {has_pending_redirect}")
                print(f"✓ Found 'Resuming interrupted flow': {has_resuming_flow}")
                print(f"{'✗' if has_my_claims_redirect else '✓'} Found 'Redirecting to My Claims page': {has_my_claims_redirect}")
                
                if has_my_claims_redirect:
                    print("\n✗ WARNING: Found My Claims redirect in console logs!")
                    test_passed = False
                
                # Wait a bit before closing
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"\n✗✗✗ TEST EXCEPTION: {str(e)}")
                self.errors.append({'step': 'test_execution', 'error': str(e)})
                test_passed = False
            
            finally:
                await browser.close()
            
            # Print final report
            self.print_report(test_passed)
            return test_passed
    
    def print_report(self, test_passed: bool):
        """Print final test report"""
        print("\n" + "="*80)
        print("TEST REPORT")
        print("="*80)
        
        print(f"\nTest Status: {'✓✓✓ PASSED ✓✓✓' if test_passed else '✗✗✗ FAILED ✗✗✗'}")
        
        print(f"\nScreenshots saved to: {self.screenshots_dir}")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        print(f"\nConsole Logs ({len(self.console_logs)}):")
        for log in self.console_logs[-20:]:  # Last 20 logs
            print(f"  [{log['type']}] {log['text']}")
        
        print("\n" + "="*80 + "\n")


async def main():
    """Main entry point"""
    test = DraftResumeTest()
    success = await test.run_test()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
