import streamlit as st
import os
import uuid
import time
import shutil

def reload_application():
    """
    This function completely reloads the application.
    It forces a complete page reload, which clears all upload fields.
    Uses a more aggressive approach to ensure file uploaders are reset.
    """
    # Clean up the downloads directory
    if os.path.exists("downloads"):
        try:
            shutil.rmtree("downloads")
            os.makedirs("downloads", exist_ok=True)
        except:
            for file in os.listdir("downloads"):
                try:
                    file_path = os.path.join("downloads", file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except:
                    pass
    
    # Create a reset flag file to signal a complete reset
    with open("reset_flag.txt", "w") as f:
        f.write(f"reset_{uuid.uuid4()}")
    
    # Clear all session state variables
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Generate a unique session ID to force new widget keys
    new_session_id = str(uuid.uuid4())
    
    # Display message
    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;align-items:center;height:100vh;">
            <div style="text-align:center;padding:20px;background-color:#f8f9fa;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <h3>Reloading application...</h3>
                <p>Please wait while the application reloads.</p>
                <p style="font-size:0.8em;color:#6c757d;">Session ID: {new_session_id}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Use JavaScript to force a complete browser reload with cache clearing
    js_code = f"""
    <script>
        // Clear all forms of browser storage
        localStorage.clear();
        sessionStorage.clear();
        
        // Clear any cached form data
        document.cookie.split(";").forEach(function(c) {{
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        }});
        
        // Attempt to clear any file input caches
        try {{
            const fileInputs = document.querySelectorAll('input[type="file"]');
            fileInputs.forEach(input => {{
                input.value = '';
            }});
        }} catch(e) {{}}
        
        // Force a complete page reload from server with unique parameters
        window.location.href = window.location.pathname + 
            "?reload=" + new Date().getTime() + 
            "&sid={new_session_id}";
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
    st.stop()

def clear_uploads():
    """
    Clear all uploaded files and force component reset without full page reload.
    """
    # Generate a new unique ID to force widget recreation
    new_run_id = str(uuid.uuid4())
    st.session_state.run_id = new_run_id
    
    # Clear all file upload related keys from session state
    for key in list(st.session_state.keys()):
        if 'uploader' in key or 'uploaded' in key:
            del st.session_state[key]
    
    # Force component to recreate with rerun
    st.rerun()

def check_for_reset_flag():
    """
    Check if a reset flag file exists and handle the reset process.
    """
    if os.path.exists("reset_flag.txt"):
        try:
            # Read the flag to get unique session ID
            with open("reset_flag.txt", "r") as f:
                reset_id = f.read().strip()
            
            # Remove the flag file
            os.remove("reset_flag.txt")
            
            # Set a completely new run ID
            st.session_state.run_id = str(uuid.uuid4())
            
            # Force reload one more time to complete the reset
            js_code = f"""
            <script>
                // Force another reload without the flag file
                window.location.href = window.location.pathname + 
                    "?complete_reset=true&ts={time.time()}&rid={reset_id}";
            </script>
            """
            st.markdown(js_code, unsafe_allow_html=True)
            st.stop()
            
        except Exception as e:
            print(f"Error handling reset flag: {e}")
            if os.path.exists("reset_flag.txt"):
                try:
                    os.remove("reset_flag.txt")
                except:
                    pass
