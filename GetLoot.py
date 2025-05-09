import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env
load_dotenv()

import openai
import streamlit as st  # ✅ Must come after dotenv but before any st.* usage
import random

# ✅ Must be the first Streamlit command
st.set_page_config(page_title="GetLoot")

# ✅ Set the API key for OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Show warning if API key is missing
if not openai.api_key:
    st.warning("⚠️ OPENAI_API_KEY not found in .env. Check your file and restart the app.")

# Display of main title
st.markdown("""
<h1 style='text-align: center; color: #bb00ff; font-size: 42px;'>
    🧿 GetLoot: Maximize DPS
</h1>
""", unsafe_allow_html=True)


st.markdown("""
<div style='padding: 10px; background-color: #111; border-radius: 8px;'>
    <p style='font-style: italic; font-size: 16px; color: #ccc; text-align: center;'>
    🎉 Congratulations, Hero. You’ve done it.<br>
    The dragons are dead, the loot is yours, and now... behold your item screen.<br>
    All thats left is to chase the best loot endlessly, and the emptiness of faster clear speed. 
    Great job beating the hit new ARPG Diablo of Exile #3. GGG / Bobby are proud of you.
    </p>
</div>
""", unsafe_allow_html=True)

# Defines the equipment slots
equipment_slots = ["Weapon", "Helmet", "Chest", "Gloves", "Boots", "Pants"]

# Defines the ranges for each stat in each equipment slot
slot_stat_ranges = {
    "Weapon": {
        "base_damage": (40, 400),
        "attack_speed": (1.0, 20.0),
        "crit_chance": (0.1, 0.9),
        "crit_damage": (2.0, 100.0),
        "element_bonus": (1.2, 40.0),
        "dot_chance": (0.1, 0.3),
    },
    "Helmet": {
        "base_damage": (10, 120),
        "attack_speed": (0.9, 20.0),
        "crit_chance": (0.05, 0.9),
        "crit_damage": (1.5, 75.0),
        "element_bonus": (1.0, 30.0),
        "dot_chance": (0.05, 0.2),
    },
    "Chest": {
        "base_damage": (20, 250),
        "attack_speed": (0.8, 30.0),
        "crit_chance": (0.03, 0.85),
        "crit_damage": (1.8, 80.0),
        "element_bonus": (1.1, 50.0),
        "dot_chance": (0.04, 0.25),
    },
    "Gloves": {
        "base_damage": (15, 180),
        "attack_speed": (1.0, 25.0),
        "crit_chance": (0.1, 0.9),
        "crit_damage": (1.6, 60.0),
        "element_bonus": (1.0, 35.0),
        "dot_chance": (0.03, 0.2),
    },
    "Boots": {
        "base_damage": (10, 150),
        "attack_speed": (1.1, 18.0),
        "crit_chance": (0.04, 0.9),
        "crit_damage": (1.3, 50.0),
        "element_bonus": (1.0, 25.0),
        "dot_chance": (0.05, 0.2),
    },
    "Pants": {
        "base_damage": (15, 200),
        "attack_speed": (1.0, 22.0),
        "crit_chance": (0.05, 0.9),
        "crit_damage": (1.7, 60.0),
        "element_bonus": (1.2, 40.0),
        "dot_chance": (0.04, 0.25),
    },
}

# Function to calculate DPS based on the gearset   
def calculate_dps(gearset):
    base_damage = 0
    attack_speed = 0
    crit_chance = 0
    crit_damage = 0
    element_bonus = 0
    dot_chance = 0

    total_items = len(gearset)

    for gear in gearset.values():
        stats = gear["stats"]
        base_damage += stats.get("base_damage", 0)
        attack_speed += stats.get("attack_speed", 0)
        crit_chance += stats.get("crit_chance", 0)
        crit_damage += stats.get("crit_damage", 0)
        element_bonus += stats.get("element_bonus", 0)
        dot_chance += stats.get("dot_chance", 0)

    attack_speed /= total_items
    crit_chance /= total_items
    crit_damage /= total_items
    element_bonus /= total_items
    dot_chance /= total_items

    dot_bonus = dot_chance * base_damage * 0.25
    dps = base_damage * (1 + crit_chance * crit_damage) * attack_speed * element_bonus + dot_bonus
    return round(dps, 2)

# This function calculates the score of an item based on its stats and the defined ranges
def get_item_score(stats, slot):
    max_score = 0
    actual_score = 0
    for stat, value in stats.items():
        low, high = slot_stat_ranges[slot][stat]
        max_score += high
        actual_score += value
    return (actual_score / max_score) * 100  # percentage

# This function generates a name for the item using GPT
def generate_item_name(slot, tier):
    prompt = get_prompt_for_tier(slot, tier)

    try:
        client = openai.OpenAI()  # use .env-loaded key by default

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative item name generator for a fantasy loot simulator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=25,
            temperature=1.0,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"❌ Error generating name for {slot} (Tier {tier}): {e}")
        return f"Unnamed {slot} (error)"
    
# This function generates a name for the full item set using GPT
def generate_gearset_name(item_names):
    joined = ", ".join(item_names)
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You name fantasy gear sets based on their individual item names."},
                {"role": "user", "content": f"Given this set of items: {joined}, generate a cool and fitting name for the full gear set."}
            ],
            max_tokens=25,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"⚠️ Error generating gear set name: {e}")
        return "Unnamed Set"


# This function gives stars based on the tier of the item
def render_item_name(name, tier):
    stars = "⭐" * tier
    color_map = {
        1: "#777777",  # Cursed
        2: "#999999",  # Trash
        3: "#aaaaaa",  # Common
        4: "#44ccff",  # Toon
        5: "#bb00ff",  # Political
        6: "#ffaa00",  # Legendary
        7: "#ffd700",  # Divine
    }
    color = color_map.get(tier, "#ffffff")
    
    return f"""
    <div style='color:{color}; font-weight:bold; text-align:center;'>
        {name}<br>
        <span style='font-size:18px;'>{stars}</span>
    </div>
    """

# This function determines the tier of an item based on its score
def get_item_tier(score):
    if score <= 10:
        return 1  # Cursed
    elif score <= 30:
        return 2  # Trash
    elif score <= 40:
        return 3  # Common
    elif score <= 60:
        return 4  # Toon
    elif score <= 80:
        return 5  # Political
    elif score <= 92:
        return 6  # Legendary
    else:
        return 7  # Divine

# This function generates a prompt for the GPT model based on the slot and tier    
def get_prompt_for_tier(slot, tier):
    prompts = {
        1: f"Generate a cursed, disgusting, or mocking item name for a {slot}. Directly insult the user for having the item. Limit the name to 6 words or fewer.",
        2: f"Generate a trashy or broken-sounding item name for a {slot}. It should feel low quality or disappointing. Limit the name to 6 words or fewer.",
        3: f"Generate a common, boring item name for a {slot}. Think basic fantasy gear. Limit the name to 6 words or fewer.",
        4: f"Generate a funny or cartoon-themed item name for a {slot}. Reference a well-known animated character, movie or tv show. Limit the name to 6 words or fewer.",
        5: f"Generate a satirical or powerful-sounding item name for a {slot} that references a real political figure. Limit the name to 6 words or fewer.",
        6: f"Generate a legendary item name for a {slot} that references a historical or mythological figure. Limit the name to 6 words or fewer.",
        7: f"Generate a divine, godlike item name for a {slot}. It should be a religious or mythical Greek God type of Name. Limit the name to 6 words or fewer.",
}   

    return prompts.get(tier, f"Generate an item name for a {slot}.")

# Function to generate a full gearset with random stats for each slot
def generate_full_gearset():
    gearset = {}

    for slot in equipment_slots:
        stats = {}
        for stat, (low, high) in slot_stat_ranges[slot].items():
            stats[stat] = round(random.uniform(low, high), 2)

        score = get_item_score(stats, slot)
        tier = get_item_tier(score)

        gearset[slot] = {
            "stats": stats,
            "score": round(score, 2),
            "tier": tier,
            "name": generate_item_name(slot, tier),
        }

    item_names = [gear["name"] for gear in gearset.values()]
    gearset_name = generate_gearset_name(item_names)
    return gearset, gearset_name


def reroll_slot(slot):
    new_stats = {
        stat: round(random.uniform(*slot_stat_ranges[slot][stat]), 2)
        for stat in slot_stat_ranges[slot]
    }

    score = get_item_score(new_stats, slot)
    tier = get_item_tier(score)
    name = generate_item_name(slot, tier)

    st.session_state.gearset[slot] = {
        "stats": new_stats,
        "score": round(score, 2),
        "tier": tier,
        "name": name,
    }

    item_names = [gear["name"] for gear in st.session_state.gearset.values()]
    st.session_state.gearset_name = generate_gearset_name(item_names)

    # ✅ Proper rerun call for latest Streamlit
    st.rerun()

    # Update gearset name
    item_names = [gear["name"] for gear in st.session_state.gearset.values()]
    st.session_state.gearset_name = generate_gearset_name(item_names)

    # 🔁 Force rerender to reflect updated slot immediately
    st.experimental_rerun()

    # 🧠 Recalculate gearset name after any reroll
    item_names = [gear["name"] for gear in st.session_state.gearset.values()]
    st.session_state.gearset_name = generate_gearset_name(item_names)

# Initialize session state variables
if "high_score" not in st.session_state:
    st.session_state.high_score = 0

if "gearset" not in st.session_state:
    gearset, gearset_name = generate_full_gearset()
    st.session_state.gearset = gearset
    st.session_state.gearset_name = gearset_name

if "gearset_name" not in st.session_state:
    st.session_state.gearset_name = "Unnamed Set"

if "high_score_set_name" not in st.session_state:
    st.session_state.high_score_set_name = "None"

st.markdown("---")

st.subheader("Your Gear")
st.markdown(f"<h3 style='text-align:center; font-style:italic'>{st.session_state.gearset_name}</h3>", unsafe_allow_html=True)

# --- Row 1: Helmet | Chest | Gloves ---
row1 = st.columns(3)

# --- Row 1: Helmet | Chest | Gloves ---
row1 = st.columns(3)

with row1[0]:  # Helmet
    gear = st.session_state.gearset["Helmet"]
    with st.expander("🪖 Helmet", expanded=True):
        st.markdown(render_item_name(gear["name"], gear["tier"]), unsafe_allow_html=True)
        for stat, value in gear["stats"].items():
            st.markdown(f"- **{stat.replace('_', ' ').title()}**: `{value}`")
        if st.button("🔄 Reroll Helmet", key="reroll_Helmet"):
            reroll_slot("Helmet")

with row1[1]:  # Chest
    gear = st.session_state.gearset["Chest"]
    with st.expander("🛡️ Chest", expanded=True):
        st.markdown(render_item_name(gear["name"], gear["tier"]), unsafe_allow_html=True)
        for stat, value in gear["stats"].items():
            st.markdown(f"- **{stat.replace('_', ' ').title()}**: `{value}`")
        if st.button("🔄 Reroll Chest", key="reroll_Chest"):
            reroll_slot("Chest")

with row1[2]:  # Gloves
    gear = st.session_state.gearset["Gloves"]
    with st.expander("🧤 Gloves", expanded=True):
        st.markdown(render_item_name(gear["name"], gear["tier"]), unsafe_allow_html=True)
        for stat, value in gear["stats"].items():
            st.markdown(f"- **{stat.replace('_', ' ').title()}**: `{value}`")
        if st.button("🔄 Reroll Gloves", key="reroll_Gloves"):
            reroll_slot("Gloves")

# --- Row 2: Weapon | Pants | Boots ---
row2 = st.columns(3)

with row2[0]:  # Weapon
    gear = st.session_state.gearset["Weapon"]
    with st.expander("🗡️ Weapon", expanded=True):
        st.markdown(render_item_name(gear["name"], gear["tier"]), unsafe_allow_html=True)
        for stat, value in gear["stats"].items():
            st.markdown(f"- **{stat.replace('_', ' ').title()}**: `{value}`")
        if st.button("🔄 Reroll Weapon", key="reroll_Weapon"):
            reroll_slot("Weapon")

with row2[1]:  # Pants
    gear = st.session_state.gearset["Pants"]
    with st.expander("👖 Pants", expanded=True):
        st.markdown(render_item_name(gear["name"], gear["tier"]), unsafe_allow_html=True)
        for stat, value in gear["stats"].items():
            st.markdown(f"- **{stat.replace('_', ' ').title()}**: `{value}`")
        if st.button("🔄 Reroll Pants", key="reroll_Pants"):
            reroll_slot("Pants")

with row2[2]:  # Boots
    gear = st.session_state.gearset["Boots"]
    with st.expander("🥾 Boots", expanded=True):
        st.markdown(render_item_name(gear["name"], gear["tier"]), unsafe_allow_html=True)
        for stat, value in gear["stats"].items():
            st.markdown(f"- **{stat.replace('_', ' ').title()}**: `{value}`")
        if st.button("🔄 Reroll Boots", key="reroll_Boots"):
            reroll_slot("Boots")

# --- DPS Calculation ---
dps = calculate_dps(st.session_state.gearset)

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f"## 🎯 Total DPS:")
    st.markdown(f"### `{dps:,.2f}`")

with col2:
    st.markdown(f"## 🏆 High Score:")
    st.markdown(f"### `{st.session_state.high_score:,.2f}`")

# --- High Score Check ---
if dps > st.session_state.high_score:
    st.session_state.high_score = dps
    st.session_state.high_score_set_name = st.session_state.gearset_name
    st.success("🔥 New High Score!")

# Optional: Show the gearset name that achieved the high score
if "high_score_set_name" in st.session_state:
    st.markdown(f"**🏅 Gearset that achieved high score:** *{st.session_state.high_score_set_name}*", unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.caption("Built in 5 days with Streamlit")


 
