#!/usr/bin/env python3
"""
Fetch Attack, Elemental Damage, and Max Ammo per unit for all players
listed in players.csv using BlablaLink's GetUserCharacterDetails endpoint.
"""

import csv
import requests
import time

API_URL = "https://api.blablalink.com/api/game/proxy/Game/GetUserCharacterDetails"
UNITS_CSV = "units.csv"
PLAYERS_CSV = "players.csv"
NIKKE_AREA_ID = 82
REQUEST_TIMEOUT = 12
SLEEP_BETWEEN_REQUESTS = 0.12


def load_units_csv(filename: str) -> dict[int, str]:
    """Load mapping from name_code -> unit name."""
    mapping: dict[int, str] = {}
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                code = int(row["units/Name code"])
                name = row["units/Name"].strip()
                mapping[code] = name
            except Exception:
                continue
    return mapping


def load_players_csv(filename: str) -> list[dict]:
    """Load players and extract intl_open_id from UID."""
    players = []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row["UID"].strip()
            # UID looks like "29080-12057416839635147011"
            intl_open_id = uid.split("-")[-1]
            players.append({
                "Player": row["Player"].strip(),
                "intl_open_id": intl_open_id
            })
    return players


def call_character_details(intl_open_id: str, name_code: int, cookie: str):
    """POST to the character details endpoint for a single name_code."""
    payload = {
        "intl_open_id": intl_open_id,
        "name_codes": [name_code],
        "nikke_area_id": NIKKE_AREA_ID,
    }
    headers = {"Content-Type": "application/json", "Cookie": cookie}
    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[ERROR] Request failed for intl_open_id={intl_open_id}, code={name_code}: {e}")
        return None


def extract_stats_per_gear(response: dict) -> dict:
    """
    Extract Attack, Elemental Damage, and AmmoLoad stats by checking
    which effect IDs are applied to each gear slot (arm, leg, head, torso).
    Each slot contributes independently, even if IDs overlap.
    """
    results = {
        "Attack": 0,
        "ElementalDamage": 0,
        "MaxAmmo": 0,
    }

    if not response:
        return results

    # --- Step 1: Build ID -> (type, value) map ---
    effect_map = {}
    state_effects = response.get("data", {}).get("state_effects", [])
    for effect in state_effects:
        eid = effect.get("id")
        for func in effect.get("function_details", []):
            ftype = func.get("function_type")
            try:
                val = int(func.get("function_value", 0))
            except Exception:
                val = 0
            effect_map[eid] = (ftype, val)

    # --- Step 2: Collect all option IDs from 4 gear slots ---
    character = response.get("data", {}).get("character_details", [{}])[0]

    gear_keys = [
        "arm_equip_option1_id", "arm_equip_option2_id", "arm_equip_option3_id",
        "leg_equip_option1_id", "leg_equip_option2_id", "leg_equip_option3_id",
        "head_equip_option1_id", "head_equip_option2_id", "head_equip_option3_id",
        "torso_equip_option1_id", "torso_equip_option2_id", "torso_equip_option3_id",
    ]

    # --- Step 3: Add up values by looking up each option ID ---
    for key in gear_keys:
        eid = str(character.get(key))  # effect IDs are strings in state_effects
        if eid in effect_map:
            ftype, val = effect_map[eid]
            if ftype == "StatAtk":
                results["Attack"] += val
            elif ftype == "IncElementDmg":
                results["ElementalDamage"] += val
            elif ftype == "StatAmmoLoad":
                results["MaxAmmo"] += val

    # --- Step 4: Scale down to proper decimals ---
    return {
        "Attack": f"{results['Attack'] / 100:.2f}",
        "ElementalDamage": f"{results['ElementalDamage'] / 100:.2f}",
        "MaxAmmo": f"{results['MaxAmmo'] / 100:.2f}",
    }



def main():
    units_map = load_units_csv(UNITS_CSV)
    players = load_players_csv(PLAYERS_CSV)
    print(f"Loaded {len(units_map)} units and {len(players)} players.")

    cookie = input("Paste your blablalink.com cookie (will not be stored): ").strip()

    out_rows = []
    total = len(players) * len(units_map)
    step = 0

    for player in players:
        player_name = player["Player"]
        intl_open_id = player["intl_open_id"]

        for name_code, unit_name in sorted(units_map.items()):
            step += 1
            print(f"[{step}/{total}] {player_name} - {unit_name} ...", end=" ")
            resp = call_character_details(intl_open_id, name_code, cookie)
            if resp and resp.get("code") == 0:
                stats = extract_stats_per_gear(resp)
                out_rows.append({
                    "Player": player_name,
                    "Unit": unit_name,
                    "Attack": stats["Attack"],
                    "ElementalDamage": stats["ElementalDamage"],
                    "MaxAmmo": stats["MaxAmmo"],
                })
                print(f"OK (Atk={stats['Attack']}, Elem={stats['ElementalDamage']}, Ammo={stats['MaxAmmo']})")
            else:
                print("FAILED or no data")
                out_rows.append({
                    "Player": player_name,
                    "Unit": unit_name,
                    "Attack": None,
                    "ElementalDamage": None,
                    "MaxAmmo": None,
                })

            time.sleep(SLEEP_BETWEEN_REQUESTS)

    out_file = "unit_stats.csv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["Player", "Unit", "Attack", "ElementalDamage", "MaxAmmo"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    print(f"Done. Results written to {out_file}")


if __name__ == "__main__":
    main()
