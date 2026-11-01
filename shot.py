import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={"width":1080,"height":1720})
    pg.goto("file:///home/claude/gude-laune/whatsapp.html"); pg.wait_for_timeout(300)
    pg.screenshot(path="whatsapp.png")
    m=b.new_page(viewport={"width":390,"height":844},device_scale_factor=2)
    m.goto("file:///home/claude/gude-laune/index.html"); m.wait_for_timeout(800)
    m.screenshot(path="page_mobile.png",full_page=False)
    m.mouse.wheel(0,1400); m.wait_for_timeout(300); m.screenshot(path="page_mobile2.png")
    b.close()
