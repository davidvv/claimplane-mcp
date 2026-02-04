"""
Browser E2E test for Step 3 Auto-save UI (WP 199)
"""
import asyncio
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import psycopg2

class AutoSaveTest:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.draft_id = "5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f"
        self.test_email = "florian.luhn@outlook.com"
        self.screenshots_dir = "/home/david/easyAirClaim/claimplane/tests/e2e/screenshots"
        self.console_logs = []
        self.errors = []
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'flight_claim',
            'user': 'postgres',
            'password': 'postgres'
        }
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def capture_console(self, msg):
        self.console_logs.append({'timestamp': datetime.now().isoformat(), 'type': msg.type, 'text': msg.text})
        print(f"[CONSOLE {msg.type.upper()}] {msg.text}")

    async def get_magic_link_token(self) -> str:
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT token FROM magic_link_tokens WHERE email = %s ORDER BY created_at DESC LIMIT 1", (self.test_email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result: return result[0]
        raise Exception(f"No magic link token found for {self.test_email}")

    async def run_test(self):
        print("\n" + "="*80)
        print("STEP 3 AUTO-SAVE UI TEST - WP 199")
        print("="*80 + "\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True) # Running headless in this environment
            context = await browser.new_context(viewport={'width': 1280, 'height': 800})
            page = await context.new_page()
            page.on("console", self.capture_console)
            
            try:
                # 1. Login flow
                print("Step 1: Logging in...")
                resume_url = f"{self.base_url}/claim/new?resume={self.draft_id}"
                await page.goto(resume_url)
                await page.wait_for_load_state('networkidle')
                
                if '/auth' in page.url:
                    print("  Redirected to auth, entering email...")
                    email_input = await page.wait_for_selector('input[type="email"]')
                    await email_input.fill(self.test_email)
                    await page.click('button[type="submit"]')
                    await asyncio.sleep(2)
                    
                    token = await self.get_magic_link_token()
                    await page.goto(f"{self.base_url}/auth/magic-link?token={token}")
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)

                print(f"  Current URL: {page.url}")
                
                # 2. Verify Step 3
                print("\nStep 2: Verifying Step 3...")
                # Wait for form to load
                first_name_input = await page.wait_for_selector('input[name="passengers.0.firstName"]')
                print("✓ Found First Name input")
                
                # 3. Change First Name to BrowserAutoSave
                print("\nStep 3: Changing First Name to 'BrowserAutoSave'...")
                await first_name_input.fill('')
                await first_name_input.type('BrowserAutoSave')
                
                # 4. Verify "Saving..." indicator
                print("Step 4: Checking for 'Saving...' indicator...")
                try:
                    saving_indicator = await page.wait_for_selector('text=Saving...', timeout=2000)
                    if saving_indicator:
                        print("✓ 'Saving...' indicator visible")
                        await page.screenshot(path=f"{self.screenshots_dir}/wp199_01_saving.png")
                except:
                    print("⚠ 'Saving...' indicator not caught (it might be too fast)")

                # 5. Verify "Saved" indicator
                print("Step 5: Checking for 'Saved' indicator...")
                saved_indicator = await page.wait_for_selector('text=Saved', timeout=5000)
                if saved_indicator:
                    print(f"✓ 'Saved' indicator visible: {await saved_indicator.inner_text()}")
                    await page.screenshot(path=f"{self.screenshots_dir}/wp199_02_saved.png")
                else:
                    print("✗ 'Saved' indicator NOT found")
                    self.errors.append("Saved indicator not found")

                # 6. Refresh page
                print("\nStep 6: Refreshing page...")
                await page.reload()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # 7. Verify persistence
                print("Step 7: Verifying persistence...")
                first_name_input = await page.wait_for_selector('input[name="passengers.0.firstName"]')
                value = await first_name_input.input_value()
                print(f"  First Name value: {value}")
                
                if value == 'BrowserAutoSave':
                    print("✓ Persistence verified")
                else:
                    print(f"✗ Persistence FAILED: expected 'BrowserAutoSave', got '{value}'")
                    self.errors.append(f"Persistence failed: {value}")

                await page.screenshot(path=f"{self.screenshots_dir}/wp199_03_after_refresh.png")

                test_passed = len(self.errors) == 0
                return test_passed

            except Exception as e:
                print(f"✗ TEST EXCEPTION: {str(e)}")
                self.errors.append(str(e))
                return False
            finally:
                await browser.close()

if __name__ == "__main__":
    test = AutoSaveTest()
    success = asyncio.run(test.run_test())
    exit(0 if success else 1)
