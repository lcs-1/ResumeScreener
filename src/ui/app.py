import streamlit as st
from io import BytesIO
import pandas as pd
from pathlib import Path
import time
import threading
import queue

def run_ui(job_descriptions, process_resumes, test_api_connectivity, api_config, processing_config):
    st.set_page_config(page_title="Resume Analysis Tool", layout="wide")
    
    # Initialize session state for persistent data
    if 'api_status_last_check' not in st.session_state:
        st.session_state.api_status_last_check = 0
        st.session_state.api_status = None
    
    if 'results_df' not in st.session_state:
        st.session_state.results_df = None
    
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
        st.session_state.files_to_process = 0
        st.session_state.files_processed = 0
    
    st.title("Resume Analysis Tool")
    st.write("Upload resumes and analyze them against a selected job description.")

    # Dashboard layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Cache job description options to prevent recomputation
        @st.cache_data(ttl=3600)  # Cache for 1 hour
        def get_jd_options():
            return list(job_descriptions.keys())
        
        jd_options = get_jd_options()
        selected_jd = st.selectbox("Select Job Description", jd_options, index=0)
        
        # File Upload with better UX
        uploaded_files = st.file_uploader(
            "Upload Resumes", 
            accept_multiple_files=True, 
            type=processing_config['supported_extensions'],
            help=f"Supported formats: {', '.join(processing_config['supported_extensions'])}. Max size: {processing_config['max_file_size_mb']}MB"
        )
        
        if uploaded_files:
            file_info = [f"{file.name} ({file.size / (1024*1024):.2f} MB)" for file in uploaded_files]
            st.write(f"📂 Uploaded {len(uploaded_files)} files:")
            
            # Show file list in a compact way
            if len(file_info) > 10:
                st.write(f"{', '.join(file_info[:3])} and {len(file_info)-3} more files")
                with st.expander("View all files"):
                    for info in file_info:
                        st.write(f"- {info}")
            else:
                for info in file_info:
                    st.write(f"- {info}")
            
            # Check file sizes before processing
            oversized_files = [f.name for f in uploaded_files if f.size > processing_config['max_file_size_mb'] * 1024 * 1024]
            if oversized_files:
                st.warning(f"⚠️ The following files exceed the maximum size limit ({processing_config['max_file_size_mb']}MB): {', '.join(oversized_files)}")
    
    with col2:
        # API Connection status - only test periodically to improve performance
        current_time = time.time()
        if current_time - st.session_state.api_status_last_check > 60:  # Test once per minute at most
            with st.spinner("Checking API connection..."):
                st.session_state.api_status = test_api_connectivity(api_config['url'], api_config['headers'])
                st.session_state.api_status_last_check = current_time
        
        api_status = st.session_state.api_status
        
        if api_status:
            st.success("API Connection: Active", icon="✅")
        else:
            st.error("API Connection: Not Available", icon="⚠️")
            if st.button("Retry Connection"):
                with st.spinner("Checking API connection..."):
                    st.session_state.api_status = test_api_connectivity(api_config['url'], api_config['headers'])
                    st.session_state.api_status_last_check = current_time
                st.experimental_rerun()
    
    # Process Button
    analyze_button = st.button(
        "Analyze Resumes", 
        disabled=(not uploaded_files or not api_status),
        use_container_width=True,
        type="primary"
    )
    
    # Processing status section
    status_container = st.container()
    
    # Handle analysis process
    if analyze_button and uploaded_files:
        # Reset state
        st.session_state.processing_status = "running"
        st.session_state.files_to_process = len(uploaded_files)
        st.session_state.files_processed = 0
        
        # Create a placeholder for manual progress tracking
        progress_bar = st.progress(0)
        status_message = st.empty()
        status_message.text(f"Starting analysis of {len(uploaded_files)} resumes...")
        
        # Process in the main thread since we can't modify the process_resumes function
        try:
            # Display estimated time
            est_time = len(uploaded_files) * (api_config['request_delay'] + 3)  # rough estimate
            status_message.text(f"Analyzing {len(uploaded_files)} resumes against '{selected_jd}' job description... (Est. time: ~{est_time} seconds)")
            
            # Process resumes (original function)
            df = process_resumes(
                uploaded_files, 
                selected_jd,
                job_descriptions,
                api_config['url'],
                api_config['headers'],
                processing_config['max_file_size_mb'],
                api_config['request_delay']
            )
            
            if df is not None and not df.empty:
                # Reorder columns according to the requested order
                ordered_columns = [
                    "Candidate Name", "Years of Experience", "JD Analyzed Against", 
                    "Most Recent Role", "Fitment Score", "Relevant Skills Matching JD",
                    "Strengths", "Gaps/Weaknesses", "Education Level", "File Name"
                ]
                
                # Make sure all columns exist (defensive programming)
                available_columns = set(df.columns)
                ordered_columns = [col for col in ordered_columns if col in available_columns]
                
                # Add any columns that might be in the dataframe but not in our ordered list at the end
                missing_columns = [col for col in df.columns if col not in ordered_columns]
                final_columns = ordered_columns + missing_columns
                
                # Reorder the DataFrame
                df = df[final_columns]
                
                st.session_state.results_df = df
                st.session_state.processing_status = "complete"
                progress_bar.progress(100)
                status_message.success(f"✅ Analysis completed for {len(df)} resumes!")
            else:
                st.session_state.processing_status = "failed"
                progress_bar.empty()
                status_message.error("❌ No results generated. Check logs for errors.")
        except Exception as e:
            st.session_state.processing_status = "failed"
            progress_bar.empty()
            status_message.error(f"❌ Error during processing: {str(e)}")
            st.error(f"Error details: {str(e)}")
    
    # Show results if available
    if st.session_state.results_df is not None:
        st.subheader("Analysis Results")
        
        df = st.session_state.results_df
        
        # Add filtering options
        col1, col2 = st.columns(2)
        with col1:
            # Convert fitment score to numeric if possible for filtering
            if 'Fitment Score' in df.columns:
                # Extract numeric values when possible
                try:
                    df['Score_Numeric'] = df['Fitment Score'].str.extract(r'(\d+)').astype(float)
                    min_score = int(df['Score_Numeric'].min() if not df['Score_Numeric'].isna().all() else 0)
                    max_score = int(df['Score_Numeric'].max() if not df['Score_Numeric'].isna().all() else 100)
                    filter_score = st.slider("Filter by Fitment Score", min_score, max_score, min_score)
                    filtered_df = df[df['Score_Numeric'] >= filter_score]
                except:
                    filtered_df = df
            else:
                filtered_df = df
        
        with col2:
            if 'Years of Experience' in df.columns:
                # Try to extract years of experience as numeric
                try:
                    df['Experience_Years'] = df['Years of Experience'].str.extract(r'(\d+)').astype(float)
                    min_exp = int(df['Experience_Years'].min() if not df['Experience_Years'].isna().all() else 0)
                    max_exp = int(df['Experience_Years'].max() if not df['Experience_Years'].isna().all() else 20)
                    filter_exp = st.slider("Filter by Years of Experience", min_exp, max_exp, min_exp)
                    filtered_df = filtered_df[filtered_df['Experience_Years'] >= filter_exp]
                except:
                    pass
        
        # Sort options
        sort_col = st.selectbox(
            "Sort results by",
            options=['Fitment Score', 'Years of Experience', 'Candidate Name', 'File Name'],
            index=0
        )
        
        # Try to sort based on numeric values when possible
        try:
            if sort_col == 'Fitment Score' and 'Score_Numeric' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('Score_Numeric', ascending=False)
            elif sort_col == 'Years of Experience' and 'Experience_Years' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('Experience_Years', ascending=False)
            else:
                filtered_df = filtered_df.sort_values(sort_col)
        except:
            pass
            
        # Display filtered dataframe (hide intermediate columns)
        display_df = filtered_df.drop(columns=['Score_Numeric', 'Experience_Years'] 
                                  if 'Score_Numeric' in filtered_df.columns and 'Experience_Years' in filtered_df.columns 
                                  else [])
        
        # Use st.dataframe with fixed height for better performance
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
        
        st.write(f"Showing {len(filtered_df)} of {len(df)} resumes")
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            # Create Excel buffer
            output_excel = BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                display_df.to_excel(writer, sheet_name='Resume Analysis', index=False)
            output_excel.seek(0)
            
            st.download_button(
                label="📊 Download as Excel",
                data=output_excel,
                file_name=processing_config['output_excel'],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            # Create CSV buffer (more lightweight)
            output_csv = BytesIO()
            display_df.to_csv(output_csv, index=False)
            output_csv.seek(0)
            
            st.download_button(
                label="📄 Download as CSV",
                data=output_csv,
                file_name=processing_config['output_excel'].replace('.xlsx', '.csv'),
                mime="text/csv",
                use_container_width=True
            )

    # Display Logs efficiently (just last 20 lines to avoid memory issues)
    with st.expander("View Recent Logs"):
        log_file = Path('logs') / 'resume_processor.log'
        if log_file.exists():
            try:
                # More efficient log reading - grab just the last N lines
                with open(log_file, 'r') as f:
                    # Get approximate file size to avoid loading huge logs
                    f.seek(0, 2)  # Go to end of file
                    file_size = f.tell()
                    
                    # If file is too big, just read the last portion
                    if file_size > 50000:  # ~50KB limit
                        f.seek(max(file_size - 50000, 0))
                        # Discard first incomplete line
                        f.readline()
                        log_content = f.read()
                    else:
                        f.seek(0)
                        log_content = f.read()
                
                # Limit to last 20 lines for display
                last_lines = log_content.split('\n')[-20:]
                st.code('\n'.join(last_lines), language="text")
            except Exception as e:
                st.error(f"Error reading logs: {e}")
        else:
            st.info("No logs available yet.")
    
    # Footer
    st.caption("Developed by ♠")
