import asyncio
import nodriver as uc

async def test():
    browser = await uc.start(headless=False)
    page = await browser.get('https://app.pixverse.ai')
    await asyncio.sleep(2)
    
    script = """
    (() => {
        window._cf_extracted_token = null;
        
        function renderTurnstile() {
            let container = document.getElementById('cf-auto-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'cf-auto-container';
                container.style = 'position: fixed; top: 120px; left: 50%; transform: translateX(-50%); z-index: 999999; background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); text-align: center;';
                document.body.appendChild(container);
            }
            if (window.turnstile) {
                try {
                    window._turnstile_widget_id = window.turnstile.render('#cf-auto-container', {
                        sitekey: '0x4AAAAAAATSS5Nb9KyiA05l',
                        callback: function(token) {
                            window._cf_extracted_token = token;
                        }
                    });
                } catch(e) {}
            }
        }
        
        if (!window.turnstile && !document.getElementById('cf-ts-tag')) {
            const s = document.createElement('script');
            s.id = 'cf-ts-tag';
            s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=cfAutoLoaded';
            s.async = true;
            window.cfAutoLoaded = function() { renderTurnstile(); };
            document.head.appendChild(s);
        } else {
            renderTurnstile();
        }
    })();
    """
    await page.evaluate(script)
    
    for i in range(25):
        await asyncio.sleep(1)
        token = await page.evaluate("window._cf_extracted_token")
        dom_token = await page.evaluate("(() => { const el = document.querySelector('[name=\"cf-turnstile-response\"]'); return el && el.value ? el.value : null; })()")
        
        # also check if iframe exists to click it if needed
        iframe_info = await page.evaluate("(() => { const f = document.querySelector('#cf-auto-container iframe'); if (!f) return null; const r = f.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; })()")
        
        print(f"Sec {i+1} | cb: {token is not None} | dom: {dom_token is not None} | iframe: {iframe_info}")
        
        if token or dom_token:
            final_token = token or dom_token
            print("\n" + "=" * 50)
            print("🎉🎉 SUCCESS! TOKEN EXTRACTED:")
            print(final_token[:60] + "...")
            print("=" * 50)
            break
            
        # If iframe exists after 3 seconds and no token, try click
        if i == 4 and iframe_info:
            print("Attempting click on iframe...")
            cx = iframe_info['x'] + 30
            cy = iframe_info['y'] + iframe_info['h'] / 2
            await page.mouse_click(cx, cy)

    browser.stop()

if __name__ == "__main__":
    asyncio.run(test())

