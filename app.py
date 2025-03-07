import streamlit as st
import tempfile
import os
import pandas as pd
from utils import process_pdf, charges_df

st.set_page_config(layout="wide", page_title="PDF Processing Application", 
                   page_icon="📄", initial_sidebar_state="collapsed")     


col1, col2 = st.columns([4, 1])
with col2:
    st.image("https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/33/53/54/335354b2-181b-fce7-fd81-c533352f8f6d/AppIcon-0-0-1x_U007epad-0-9-0-0-85-220.png/434x0w.webp", width=100) 

with col1:
    st.title("")

def main():
    st.subheader("correct invoice amount calculator for vehicle charges")

    # Sidebar to show Vehicle Charges DataFrame
    st.sidebar.header("Vehicle Charges")
    st.sidebar.dataframe(charges_df)

    # File uploader
    col1, col2 = st.columns([0.4, 1])
    with col1:
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", )


    with col2:
        st.write("")        
    if uploaded_file is not None:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            # Process the PDF
            processed_df, totals_dict = process_pdf(tmp_file_path)

            # Display processed DataFrame
            st.header("Processed PDF Data")
            st.dataframe(processed_df)

            # Display totals
            st.header("Financial Totals")
            if totals_dict:
                for key, value in totals_dict.items():
                    st.write(f"{key}: {value}")
            else:
                st.write("No totals found in the PDF")

            # Download button for processed DataFrame
            csv = processed_df.to_csv(index=False)
            st.download_button(
                label="Download Processed Data as CSV",
                data=csv,
                file_name="processed_pdf_data.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"An error occurred while processing the PDF: {e}")

        finally:
            # Clean up the temporary file
            os.unlink(tmp_file_path)

if __name__ == "__main__":
    main()