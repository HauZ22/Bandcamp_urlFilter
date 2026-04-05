import os

import streamlit as st
from dotenv import load_dotenv

from app_modules.filtering import validate_filters
from app_modules.streamrip import (
    CODEC_OPTIONS,
    QUALITY_OPTIONS,
    ensure_streamrip_config_file,
    format_quality_option,
    get_env_qobuz_values,
    get_streamrip_config_path,
    load_streamrip_settings,
    save_streamrip_settings,
)
from app_modules.system_utils import open_in_default_app
from app_modules.ui_processing import (
    handle_process_submission,
    render_results_and_exports,
    render_status_log,
    run_processing_tick,
)
from app_modules.ui_state import init_session_state
from app_modules.ui_streamrip_setup import init_streamrip_download_state, render_streamrip_setup

load_dotenv()

st.set_page_config(page_title="Bandcamp to Qobuz Matcher", layout="wide")
st.title("🎵 Bandcamp to Qobuz Matcher")
st.markdown("Filter your Bandcamp URLs and find exact high-resolution matches on Qobuz.")

init_session_state()

st.sidebar.header("Configuration")

with st.sidebar.expander("🎯 Filter Rules", expanded=True):
    tag_input = st.text_input("Genre / Tag", value="", help="Filter by tag or genre.")
    location_input = st.text_input("Location", value="", help="Filter by location text in metadata.")
    min_tracks = st.number_input("Min Tracks", min_value=1, value=None, step=1, help="Leave empty for no minimum.")
    max_tracks = st.number_input("Max Tracks", min_value=1, value=None, step=1, help="Leave empty for no maximum.")
    min_duration = st.number_input("Min Duration (min)", min_value=1, value=None, step=1, help="Leave empty for no minimum.")
    max_duration = st.number_input("Max Duration (min)", min_value=1, value=None, step=1, help="Leave empty for no maximum.")

with st.sidebar.expander("📅 Release Date", expanded=False):
    start_date = st.date_input("Start Date", value=None, help="Filter for releases on or after this date.")
    end_date = st.date_input("End Date", value=None, help="Filter for releases on or before this date.")

with st.sidebar.expander("⚙️ Run Settings", expanded=True):
    free_mode = st.selectbox("Pricing", options=["All", "Free", "Paid"], index=0)
    dry_run = st.checkbox("Dry Run", value=False, help="Only apply Bandcamp filter, skip Qobuz search.")
    if st.button("📝 Open .env for Qobuz Token"):
        env_path = ".env"
        if not os.path.exists(env_path):
            template = """# Important: So that Python recognizes local directories (e.g., logic) as modules
PYTHONPATH=.
# Optional: Set your own Qobuz App ID (if omitted, the app auto-fetches it from Qobuz Web Player)
# QOBUZ_APP_ID=
# Required (depending on region/account type): Set your user Auth Token for Qobuz
QOBUZ_USER_AUTH_TOKEN="""
            try:
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(template)
            except Exception as e:
                st.error(f"Error creating the .env file: {e}")

        try:
            open_in_default_app(env_path)
        except Exception as e:
            st.error(f"Could not open .env: {e}")

streamrip_config_path = get_streamrip_config_path()
streamrip_config_ready, streamrip_config_init_msg = ensure_streamrip_config_file(streamrip_config_path)
streamrip_settings = {}
streamrip_settings_error = ""
if streamrip_config_ready:
    streamrip_settings, streamrip_settings_error = load_streamrip_settings(streamrip_config_path)
env_qobuz_app_id, env_qobuz_token = get_env_qobuz_values()

if streamrip_config_ready and streamrip_settings and env_qobuz_token:
    needs_token = not str(streamrip_settings.get("password_or_token", "")).strip()
    needs_app_id = bool(env_qobuz_app_id) and not str(streamrip_settings.get("app_id", "")).strip()
    if needs_token or needs_app_id:
        _ok, _msg = save_streamrip_settings(
            streamrip_config_path,
            use_auth_token=True,
            email_or_userid=str(streamrip_settings.get("email_or_userid", "")),
            password_or_token=env_qobuz_token,
            app_id=env_qobuz_app_id or str(streamrip_settings.get("app_id", "")),
            quality=int(streamrip_settings.get("quality", 3)),
            codec_selection=str(streamrip_settings.get("codec_selection", "Original")),
            downloads_folder=str(streamrip_settings.get("downloads_folder", "")),
        )
        if _ok:
            streamrip_settings, streamrip_settings_error = load_streamrip_settings(streamrip_config_path)

if streamrip_config_init_msg:
    st.sidebar.info(streamrip_config_init_msg)
if streamrip_settings_error:
    st.sidebar.warning(streamrip_settings_error)

default_rip_quality = int(streamrip_settings.get("quality", 3)) if streamrip_settings else 3
if default_rip_quality not in QUALITY_OPTIONS:
    default_rip_quality = 3

default_codec = str(streamrip_settings.get("codec_selection", "Original")) if streamrip_settings else "Original"
if default_codec not in CODEC_OPTIONS:
    default_codec = "Original"

default_downloads_folder = str(streamrip_settings.get("downloads_folder", "")).strip() if streamrip_settings else ""
init_streamrip_download_state(default_downloads_folder)

with st.sidebar.expander("⚙️ Streamrip Settings", expanded=False):
    rip_quality = st.selectbox(
        "Rip Quality",
        options=QUALITY_OPTIONS,
        index=QUALITY_OPTIONS.index(default_rip_quality),
        format_func=format_quality_option,
        help="Applied to rip commands (equivalent to --quality).",
    )
    rip_codec = st.selectbox(
        "Rip Codec",
        options=CODEC_OPTIONS,
        index=CODEC_OPTIONS.index(default_codec),
        help="Applied to rip commands (equivalent to --codec). Use Original for no conversion flag.",
    )
    st.caption("Qobuz and Tidal ripping requires a premium subscription.")

uploaded_file = st.file_uploader("Upload .txt or .log file with Bandcamp URLs", type=["txt", "log"])

has_streamrip_identifier = bool(str(streamrip_settings.get("email_or_userid", "")).strip())
has_streamrip_token = bool(str(streamrip_settings.get("password_or_token", "")).strip())
streamrip_needs_setup = (
    not streamrip_config_ready
    or not streamrip_settings
    or not (has_streamrip_identifier and has_streamrip_token)
)

render_streamrip_setup(
    streamrip_needs_setup=streamrip_needs_setup,
    streamrip_config_path=streamrip_config_path,
    streamrip_config_ready=streamrip_config_ready,
    streamrip_settings=streamrip_settings,
    default_rip_quality=default_rip_quality,
    default_codec=default_codec,
    env_qobuz_app_id=env_qobuz_app_id,
    env_qobuz_token=env_qobuz_token,
)

validation_errors = validate_filters(
    min_tracks,
    max_tracks,
    min_duration,
    max_duration,
    start_date,
    end_date,
)
if validation_errors:
    for err in validation_errors:
        st.error(err)

filter_config = {
    "tag": tag_input,
    "location": location_input,
    "min_tracks": int(min_tracks) if min_tracks else None,
    "max_tracks": int(max_tracks) if max_tracks else None,
    "min_duration": int(min_duration) if min_duration else None,
    "max_duration": int(max_duration) if max_duration else None,
    "free_mode": free_mode,
}

col1, col2, col3 = st.columns([1.2, 1.6, 4])
with col1:
    process_btn = st.button("Process", type="primary", disabled=bool(validation_errors))
with col2:
    auto_rip_after_export = st.toggle(
        "Auto rip after export",
        value=False,
        help="Automatically run streamrip after exporting this run's Qobuz results.",
    )
with col3:
    stop_btn = st.button(
        "Stop / Cancel",
        help="Stops after the current in-flight batch and shows partial results.",
        disabled=not st.session_state.processing,
    )

if stop_btn and st.session_state.processing:
    st.session_state.cancel_requested = True
    st.info("Stop requested. Processing will end after the current batch.")

handle_process_submission(
    process_btn=process_btn,
    uploaded_file=uploaded_file,
    filter_config=filter_config,
    start_date=start_date,
    end_date=end_date,
    dry_run=dry_run,
)

run_processing_tick()
render_status_log(dry_run=dry_run)
render_results_and_exports(
    dry_run=dry_run,
    rip_quality=rip_quality,
    rip_codec=rip_codec,
    auto_rip_after_export=auto_rip_after_export,
)
