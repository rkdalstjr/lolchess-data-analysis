# crawler.py
import json
import re
import time
from playwright.sync_api import sync_playwright

def crawl_recent_win_decks():
    with sync_playwright() as p:
        # 헤드리스 브라우저 실행
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("🌐 페이지 로딩 중...")
        page.goto("https://lolchess.gg/recent-win-decks", wait_until="networkidle")
        
        # 동적 렌더링 대기
        time.sleep(5)
        
        # 1) 모든 덱 카드 찾기 (match-info 영역)
        deck_cards = page.query_selector_all('div.match-info')
        print(f"🔍 총 {len(deck_cards)}개 덱 발견")
        
        decks_data = []
        
        for idx, card in enumerate(deck_cards[:10], 1):  # 최대 10개
            try:
                # ---------- 상위 부모로 올라가서 플레이어/티어 정보 추출 ----------
                parent = card.query_selector('xpath=..')  # div.match-info의 부모 요소
                player = "UnknownPlayer"
                tier = "UnknownTier"
                
                if parent:
                    # 실제 HTML 구조에 맞춘 정확한 선택자 사용
                    player_el = parent.query_selector('.nickname .gamename')
                    if player_el:
                        player = player_el.inner_text().strip()
                    
                    tier_el = parent.query_selector('.tier')
                    if tier_el:
                        tier = tier_el.inner_text().strip()
                
                # ---------- 시너지(Traits) 추출 ----------
                trait_imgs = card.query_selector_all('div.TraitItem img')
                trait_names = []
                for img in trait_imgs:
                    src = img.get_attribute('src') or ""
                    match = re.search(r'traits/([^/]+)_black', src)
                    if match:
                        trait_names.append(match.group(1))
                
                # ---------- 챔피언(Champions) 및 아이템(Items) 추출 ----------
                champion_imgs = card.query_selector_all('div.Champion div.champion-portrait div.inner-content img')
                champion_names = []
                for img in champion_imgs:
                    src = img.get_attribute('src') or ""
                    match = re.search(r'champions/TFT17_(\w+)\.jpg', src)
                    if match:
                        champion_names.append(match.group(1))
                
                item_imgs = card.query_selector_all('div.Champion div.items div.item img')
                item_names = []
                for img in item_imgs:
                    src = img.get_attribute('src') or ""
                    match = re.search(r'items/([^/]+)\.png', src)
                    if match:
                        item_names.append(match.group(1))
                
                # ---------- preprocess.py가 이해하는 markdown 형식으로 조립 ----------
                markdown = f"#1 플레이어 profile/123/{player} ({tier}) "
                markdown += " ".join([f"champions/TFT17_{champ}.jpg" for champ in champion_names[:8]])
                markdown += " " + " ".join([f"items/{item}.png" for item in item_names[:6]])
                markdown += " " + " ".join([f"traits/{trait}_black" for trait in trait_names[:6]])
                
                decks_data.append({"markdown": markdown})
                print(f"  ✅ 덱 #{idx}: {player} ({tier}) - 챔피언 {len(champion_names)}개")
                
            except Exception as e:
                print(f"  ❌ 덱 #{idx} 파싱 중 오류: {e}")
                continue
        
        browser.close()
    
    # JSON 파일로 저장
    output = {"results": decks_data}
    with open('/data/input.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 총 {len(decks_data)}개 덱 크롤링 완료 → /data/input.json")

if __name__ == "__main__":
    crawl_recent_win_decks()