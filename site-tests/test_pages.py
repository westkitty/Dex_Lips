"""Actual-browser smoke test of the public static rig editor. No external services."""
from __future__ import annotations
import hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import threading
import tempfile
import zipfile
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'site'

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args):pass

def fixture(root:Path, *, bright=False, blank=False)->Path:
    fn=root/('light.png' if bright else ('blank.png' if blank else 'dark.png'))
    base=(19,33,61) if bright else (181,156,120)
    img=Image.new('RGB',(320,240),base)
    if not blank:
        d=ImageDraw.Draw(img)
        d.polygon([(132,148),(143,132),(160,140),(182,133),(189,153),(163,161),(141,158)],fill=(16,232,244) if bright else (20,28,46))
    img.save(fn)
    return fn

def slider(page, element_id: str, value: str):
    page.locator(f'#{element_id}').evaluate("(el,v) => {el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));}", value)

def main():
    h=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    t=threading.Thread(target=h.serve_forever,daemon=True);t.start()
    url=f'http://127.0.0.1:{h.server_port}/'
    with tempfile.TemporaryDirectory() as d, sync_playwright() as p:
        root=Path(d)
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':960},accept_downloads=True)
        errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
        page.goto(url)
        assert page.title()=='Dex_Lips — Mouth Rig Lab'
        source=fixture(root)
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        page.locator('#sourceInput').set_input_files(str(source))
        page.locator('#generate').wait_for(state='visible')
        page.wait_for_function('!document.querySelector("#generate").disabled')
        slider(page,'mouthW','29');slider(page,'mouthH','20');slider(page,'mouthY','61');
        page.locator('#generate').click()
        page.wait_for_function('document.querySelector("#traceState").textContent === "SOURCE TRACE"')
        assert 'Nine separate' in page.locator('#message').inner_text()
        assert 'SOURCE TRACE' in page.locator('#traceState').inner_text()
        page.screenshot(path=str(root/'desktop.png'),full_page=True)
        page.locator('#reviewed').check()
        with page.expect_download() as download_info:page.locator('#downloadZip').click()
        dl=download_info.value
        target=root/dl.suggested_filename
        dl.save_as(target)
        with zipfile.ZipFile(target) as archive:
            names=set(archive.namelist())
            assert names=={f'{s}.png' for s in 'XABCDEFGH'}|{'rig.json'},names
            rig=json.loads(archive.read('rig.json'))
            assert rig['source_sha256']==digest
            assert rig['authority']=='generated_draft' and rig['approved'] is False
            for letter in 'XABCDEFGH':
                fn=root/f'{letter}.png';fn.write_bytes(archive.read(f'{letter}.png'))
                with Image.open(fn) as image:assert image.mode=='RGBA'
        assert target.stat().st_size>1000
        # Changing parameters invalidates prior acceptance/export as it must.
        slider(page,'mouthX','52')
        assert page.locator('#downloadZip').is_disabled()
        page.locator('#sourceInput').set_input_files(str(fixture(root,blank=True)))
        page.wait_for_function('!document.querySelector("#generate").disabled')
        page.locator('#generate').click()
        assert 'No isolated mouth' in page.locator('#message').inner_text()
        assert page.locator('#downloadZip').is_disabled()
        page.locator('#mode').select_option('faceted')
        page.locator('#generate').click()
        assert 'Nine separate mouth sprites' in page.locator('#message').inner_text()
        # Bright mouth on dark facial art.
        page.locator('#sourceInput').set_input_files(str(fixture(root,bright=True)))
        page.wait_for_function('!document.querySelector("#generate").disabled')
        page.locator('#mode').select_option('source-faceted')
        page.locator('#contrast').select_option('light')
        slider(page,'mouthX','50')
        page.locator('#generate').click()
        assert 'Nine separate mouth sprites' in page.locator('#message').inner_text(),page.locator('#message').inner_text()
        assert not errors,errors
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(root/'mobile.png'),full_page=True)
        # CSS width guard against horizontal overflow.
        overflow=page.evaluate('document.documentElement.scrollWidth>window.innerWidth+1')
        assert not overflow,'mobile layout overflows horizontally'
        print(json.dumps({'result':'PASS','url':url,'download_size':target.stat().st_size,'zip_entries':sorted(names),'original_sha256':digest,'javascript_errors':errors,'horizontal_overflow':overflow,'screenshots':{'desktop':str(root/'desktop.png'),'mobile':str(root/'mobile.png')}}))
        browser.close()
    h.shutdown()

if __name__=='__main__':main()