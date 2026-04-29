import streamlit as st
import os
from pawpal_system import Task, Pet, Owner, Scheduler

# --- 1. Page Configuration & Professional Styling ---
st.set_page_config(page_title="PawPal+ Professional", page_icon="🐾", layout="wide")

# Custom CSS for a clean, card-based interface
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    [data-testid="stExpander"] { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Logic Helpers for UI ---
def get_task_icon(description):
    """Assigns an emoji based on common keywords in the task description."""
    desc = description.lower()
    if any(word in desc for word in ["walk", "run", "park", "play"]): return "🏃"
    if any(word in desc for word in ["feed", "food", "dinner", "breakfast", "treat"]): return "🥣"
    if any(word in desc for word in ["med", "pill", "vet", "doctor", "heartworm"]): return "💊"
    if any(word in desc for word in ["bath", "groom", "brush", "nail"]): return "🛁"
    return "📝"

# --- 3. Smart Initialization ---
if 'owner' not in st.session_state:
    if os.path.exists("data.json"):
        st.session_state.owner = Owner.load_from_json("data.json")
    else:
        st.session_state.owner = Owner(name="Kamayani", available_time_mins=180)
        st.session_state.owner.add_pet(Pet(name="Mochi", species="Dog", age=3))
    
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)

# --- 4. Dashboard Header & Metrics ---
st.title("🐾 PawPal+ Pro Dashboard")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Active Owner", st.session_state.owner.name)
with m2:
    st.metric("Time Budget", f"{st.session_state.owner.available_time_mins}m")
with m3:
    pending_count = len(st.session_state.scheduler.get_tasks_by_status(False))
    st.metric("Pending Tasks", pending_count)

st.divider()

# --- 5. Sidebar: Assistant Tools ---
with st.sidebar:
    st.header("✨ Smart Tools")
    with st.container(border=True):
        st.write("Find a free window:")
        slot_dur = st.number_input("Mins needed", 15, 120, 30, 15)
        if st.button("🔍 Scan Schedule"):
            res = st.session_state.scheduler.find_next_available_slot(slot_dur)
            st.success(f"Gap at {res}") if ":" in res else st.warning(res)
    
    st.divider()
    if st.button("🗑️ Reset All Data", type="secondary"):
        if os.path.exists("data.json"): os.remove("data.json")
        st.rerun()

# --- 6. Task Management ---
col_input, col_display = st.columns([1, 2])

with col_input:
    st.subheader("➕ New Activity")
    with st.form("task_form", clear_on_submit=True):
        title = st.text_input("Task Name", placeholder="e.g. Heartworm Pill")
        time_val = st.text_input("Time (HH:MM)", value="09:00")
        dur_val = st.number_input("Duration (mins)", 5, 180, 20)
        prio_val = st.select_slider("Priority Level", options=["low", "medium", "high"], value="medium")
        freq_val = st.selectbox("Frequency", ["Once", "Daily", "Weekly"])
        
        if st.form_submit_button("Add to Vault"):
            new_t = Task(title, int(dur_val), prio_val, freq_val, time_val)
            conflict = st.session_state.scheduler.check_conflicts(new_t)
            if conflict:
                st.error(conflict, icon="🚨")
            else:
                st.session_state.owner.pets[0].add_task(new_t)
                st.session_state.owner.save_to_json()
                st.rerun()

with col_display:
    tab1, tab2 = st.tabs(["📋 Current List", "🚀 Optimized Plan"])
    
    with tab1:
        pending = st.session_state.scheduler.get_tasks_by_status(False)
        if not pending:
            st.info("No pending tasks!")
        else:
            for t in pending:
                icon = get_task_icon(t.description)
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        # Status indicator logic
                        prio_color = "🔴" if t.priority == "high" else "🟡" if t.priority == "medium" else "🔵"
                        st.markdown(f"### {icon} {t.description}")
                        st.write(f"{prio_color} **{t.priority.upper()}** | ⏰ {t.due_time} | ⏳ {t.duration_mins}m")
                    with c2:
                        if st.button("Done", key=t.id):
                            st.session_state.scheduler.complete_task(t.id)
                            st.session_state.owner.save_to_json()
                            st.rerun()

    with tab2:
        if st.button("Generate Smart Schedule"):
            raw = st.session_state.scheduler.generate_daily_schedule()
            # Multi-level sort: Priority (High->Low) then Time
            p_map = {"high": 0, "medium": 1, "low": 2}
            sorted_plan = sorted(raw, key=lambda x: (p_map.get(x.priority.lower(), 3), x.due_time))
            
            if not sorted_plan:
                st.warning("No tasks fit your budget today.")
            else:
                for t in sorted_plan:
                    icon = get_task_icon(t.description)
                    # Professional Color-coded indicators
                    if t.priority == "high":
                        st.error(f"**{t.due_time}** | {icon} {t.description} (CRITICAL)")
                    elif t.priority == "medium":
                        st.warning(f"**{t.due_time}** | {icon} {t.description} (REQUIRED)")
                    else:
                        st.info(f"**{t.due_time}** | {icon} {t.description} (ROUTINE)")