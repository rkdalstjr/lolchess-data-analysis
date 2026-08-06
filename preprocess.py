# preprocess.py
import json
import pandas as pd
import re
import sys
from pathlib import Path

def process_lolchess_data(input_file, output_file=None):
    """
    롤체지지 RAW 데이터를 CSV로 변환
    """
    # 출력 파일명이 없으면 입력 파일명 기반으로 생성
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_processed.csv"
    
    # 1. JSON 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 2. 마크다운 내용 추출
    markdown = data['results'][0]['markdown']
    
    # 3. 덱 블록 분리 (#1, #2, #3 ...)
    deck_blocks = re.split(r'#\d+\s+', markdown)[1:]
    
    # 4. 각 덱에서 정보 추출
    decks = []
    for deck in deck_blocks:
        # 플레이어 이름
        player_match = re.search(r'profile/[^/]+/([^)]+)', deck)
        player = player_match.group(1) if player_match else "Unknown"
        
        # 티어
        tier_match = re.search(r'(GM|M|C|Challenger|Grandmaster|Master)', deck)
        tier = tier_match.group(1) if tier_match else "Unknown"
        
        # 챔피언 목록
        champs = re.findall(r'champions/TFT17_(\w+)\.jpg', deck)
        
        # 아이템 목록
        items = re.findall(r'items/([^/]+)\.png', deck)
        
        # 시너지 목록
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
    
    # 5. CSV 저장
    df = pd.DataFrame(decks)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ {len(decks)}개 덱 처리 완료 → {output_file}")
    return df

if __name__ == "__main__":
    # 커맨드라인 인자 처리
    if len(sys.argv) < 2:
        print("사용법: python preprocess.py <input_json> [output_csv]")
        print("예시: python preprocess.py raw_data.json processed_decks.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_lolchess_data(input_file, output_file)