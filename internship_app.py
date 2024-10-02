import streamlit as st
import pandas as pd
import re

# Function to read the Excel file
def read_excel_data(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"Error reading the Excel file: {e}")
        return pd.DataFrame()

# Function to normalize and clean company names (remove spaces, capitalization)
def clean_company_name(name):
    return re.sub(r'\s+', '', name.lower().strip())

# Function to extract company name before the first dash
def extract_company_name(text):
    if '-' in text:
        return text.split('-')[0].strip()
    return text.strip()

# Function to categorize internships based on pay
def categorize_internships(internships, excel_data, threshold=50):
    above_threshold = []
    below_threshold = []
    not_found = []
    
    # Clean and normalize company names in the Excel data
    excel_data['cleaned_company'] = excel_data['Company'].apply(clean_company_name)
    
    for internship in internships:
        company_name = extract_company_name(internship)
        cleaned_name = clean_company_name(company_name)
        
        # Match based on cleaned names
        match = excel_data[excel_data['cleaned_company'] == cleaned_name]
        
        if not match.empty:
            pay = match.iloc[0]['Hourly Salary']
            if pay >= threshold:
                above_threshold.append((internship, f"${pay}/hr"))
            else:
                below_threshold.append((internship, f"${pay}/hr"))
        else:
            not_found.append(internship)
    
    return above_threshold, below_threshold, not_found

# Main Streamlit app
def main():
    st.title("Internship Salary Checker")
    
    st.markdown("""
    **Instructions:**
    1. Enter each internship on a new line in the format:
       ```
       Company Name - Random Information
       ```
       Example:
       ```
       Radix Trading
       DE.. Shaw - with Fuzzy Match
       Virtu Financial - Summer 2025 Internship
       Amazon - Quantitative Researcher
       Honeywell - Quantitative Researcher
       Spectrum - CEO - Intern
       Somos Inc. - Software Engineer Intern
       ```
    2. Click "Check Salaries" to see the categorization of internships.
    """)

    # File path for Excel data
    excel_file = "levels_data.xlsx"

    # Read the Excel data
    excel_data = read_excel_data(excel_file)
    if excel_data.empty:
        st.error("No valid data found in the Excel file.")
        return

    # User input for internship list
    internship_input = st.text_area(
        "Enter Internship Company Names and Info (One per line)",
        height=200,
        placeholder="Radix Trading\nVirtu Financial - Summer 2025 Internship\nAmazon - Quantitative Researcher\nHoneywell - Quantitative Researcher\nSpectrum - CEO - Intern\nSomos Inc. - Software Engineer Intern"
    )

    if st.button("Check Salaries"):
        if not internship_input.strip():
            st.warning("Please enter internship company names.")
            return
        
        # Split user input into a list of company names
        internships = internship_input.strip().split('\n')

        # Categorize internships
        above_threshold, below_threshold, not_found = categorize_internships(internships, excel_data)

        # Display results
        st.subheader("Internships That Pay Above Your Threshold ($50/hr):")
        if above_threshold:
            above_df = pd.DataFrame(above_threshold, columns=["Company Info", "Hourly Pay"])
            st.dataframe(above_df)
        else:
            st.info("No internships found that meet the pay threshold.")

        st.subheader("Internships That Pay Below Your Threshold ($50/hr):")
        if below_threshold:
            below_df = pd.DataFrame(below_threshold, columns=["Company Info", "Hourly Pay"])
            st.dataframe(below_df)
        else:
            st.info("No internships found that pay below the threshold.")

        st.subheader("Internships That We Couldn't Find Data For:")
        if not_found:
            not_found_df = pd.DataFrame(not_found, columns=["Company Info"])
            st.dataframe(not_found_df)
        else:
            st.info("All internships were found in the data.")

if __name__ == "__main__":
    main()