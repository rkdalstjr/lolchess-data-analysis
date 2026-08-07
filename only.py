# only.py - 통합 실행 스크립트 (Docker 필요 없음)
import json
import re
import time
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright

# ==========================================
# 1. 크롤링 함수 (lolchess.gg/recent-win-decks)
# ==========================================
def crawl_recent_win_decks(output_file="input.json"):
    print("🌐 크롤링 시작: lolchess.gg/recent-win-decks ...")
    
    with sync_playwright() as p:
        # 헤드리스 브라우저 실행 (로컬에서는 창이 안 뜨고 백그라운드에서 돕니다)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://lolchess.gg/recent-win-decks", wait_until="networkidle")
        time.sleep(5)  # 동적 콘텐츠 로딩 대기
        
        deck_cards = page.query_selector_all('div.match-info')
        print(f"🔍 총 {len(deck_cards)}개 덱 발견")
        
        decks_data = []
        for idx, card in enumerate(deck_cards[:10], 1):
            try:
                # --- 플레이어/티어 정보 (상위 부모에서 추출) ---
                parent = card.query_selector('xpath=..')
                player = "Unknown"
                tier = "Unknown"
                if parent:
                    player_el = parent.query_selector('.nickname .gamename')
                    if player_el:
                        player = player_el.inner_text().strip()
                    tier_el = parent.query_selector('.tier')
                    if tier_el:
                        tier = tier_el.inner_text().strip()
                
                # --- 시너지 추출 (Traits) ---
                trait_imgs = card.query_selector_all('div.TraitItem img')
                trait_names = []
                for img in trait_imgs:
                    src = img.get_attribute('src') or ""
                    match = re.search(r'traits/([^/]+)_black', src)
                    if match:
                        trait_names.append(match.group(1))
                
                # --- 챔피언 추출 (Champions) ---
                champ_imgs = card.query_selector_all('div.Champion div.champion-portrait img')
                champ_names = []
                for img in champ_imgs:
                    src = img.get_attribute('src') or ""
                    match = re.search(r'champions/TFT17_(\w+)\.jpg', src)
                    if match:
                        champ_names.append(match.group(1))
                
                # --- 아이템 추출 (Items) ---
                item_imgs = card.query_selector_all('div.Champion div.items div.item img')
                item_names = []
                for img in item_imgs:
                    src = img.get_attribute('src') or ""
                    match = re.search(r'items/([^/]+)\.png', src)
                    if match:
                        item_names.append(match.group(1))
                
                # --- preprocess가 이해하는 Markdown 형식으로 조립 ---
                markdown = f"#1 플레이어 profile/123/{player} ({tier}) "
                markdown += " ".join([f"champions/TFT17_{champ}.jpg" for champ in champ_names[:8]])
                markdown += " " + " ".join([f"items/{item}.png" for item in item_names[:6]])
                markdown += " " + " ".join([f"traits/{trait}_black" for trait in trait_names[:6]])
                
                decks_data.append({"markdown": markdown})
                print(f"  ✅ 덱 #{idx}: {player} ({tier}) - 챔피언 {len(champ_names)}개")
                
            except Exception as e:
                print(f"  ❌ 덱 #{idx} 오류: {e}")
                continue
        
        browser.close()
    
    # JSON 파일로 저장 (같은 폴더에 input.json 생성)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"results": decks_data}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 크롤링 완료! ({len(decks_data)}개 덱) → {output_file}")

# ==========================================
# 2. 전처리 함수 (CSV 변환)
# ==========================================
def process_lolchess_data(input_file="input.json", output_file="output.csv"):
    print("🔄 전처리 시작: JSON → CSV 변환...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    markdown = data['results'][0]['markdown']
    deck_blocks = re.split(r'#\d+\s+', markdown)[1:]
    
    decks = []
    for deck in deck_blocks:
        player_match = re.search(r'profile/[^/]+/([^)]+)', deck)
        player = player_match.group(1) if player_match else "Unknown"
        
        tier_match = re.search(r'(GM|M|C|Challenger|Grandmaster|Master)', deck)
        tier = tier_match.group(1) if tier_match else "Unknown"
        
        champs = re.findall(r'champions/TFT17_(\w+)\.jpg', deck)
        items = re.findall(r'items/([^/]+)\.png', deck)
        traits = re.findall(r'traits/(\w+)_black', deck)
        
        decks.append({
            "player": player,
            "tier": tier,
            "champion_count": len(champs),
            "item_count": len(items),
            "trait_count": len(traits),
            "champions": ", ".join(champs[:8]),
            "items": ", ".join(items[:6]),
            "traits": ", ".join(traits[:6])
        })
    
    df = pd.DataFrame(decks)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 전처리 완료! → {output_file}")

# ==========================================
# 3. 메인 실행 (한방에!)
# ==========================================
if __name__ == "__main__":
    # 1) 크롤링 실행 (input.json 생성)
    crawl_recent_win_decks("input.json")
    
    # 2) 전처리 실행 (output.csv 생성)
    process_lolchess_data("input.json", "output.csv")
    
    print("\n🎉 모든 작업이 완료되었습니다. output.csv 파일을 확인하세요!")