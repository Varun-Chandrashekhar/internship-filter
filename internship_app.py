import streamlit as st
import pandas as pd
import re
from fuzzywuzzy import process

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

# Function to match based on the first word
def match_based_on_first_word(company_name, excel_data, threshold=80):
    first_word = company_name.split()[0].lower().strip()  # Extract the first word
    # Use fuzzy matching to find the closest match to the first word
    choices = excel_data['Company'].apply(lambda x: x.split()[0].lower().strip()).tolist()
    best_match, score = process.extractOne(first_word, choices)
    
    if score >= threshold:
        matched_row = excel_data[excel_data['Company'].apply(lambda x: x.split()[0].lower().strip()) == best_match]
        return matched_row.iloc[0] if not matched_row.empty else None
    return None

# Fuzzy matching function
def fuzzy_match_company_name(company_name, excel_data, threshold=80):
    cleaned_name = clean_company_name(company_name)
    # Create a list of cleaned company names from the excel data
    choices = excel_data['Company'].apply(clean_company_name).tolist()
    
    # Use fuzzy matching to find the closest match
    best_match, score = process.extractOne(cleaned_name, choices)
    
    if score >= threshold:  # Only consider matches above the threshold
        matched_row = excel_data[excel_data['Company'].apply(clean_company_name) == best_match]
        return matched_row.iloc[0] if not matched_row.empty else None
    return match_based_on_first_word(company_name, excel_data, threshold)  # Fallback to first-word matching

# Function to calculate what percentage of companies are below the threshold
def calculate_threshold_percentage(excel_data, threshold):
    total_companies = len(excel_data)
    below_threshold = len(excel_data[excel_data['Hourly Salary'] < threshold])
    percentage = (below_threshold / total_companies) * 100
    return 100 - percentage  # Percentage above the threshold

# Function to categorize internships based on pay using fuzzy matching
def categorize_internships(internships, excel_data, threshold=50, fuzzy_threshold=80):
    above_threshold = []
    below_threshold = []
    not_found = []
    
    for internship in internships:
        company_name = extract_company_name(internship)
        matched_row = fuzzy_match_company_name(company_name, excel_data, fuzzy_threshold)
        
        if matched_row is not None:
            pay = matched_row['Hourly Salary']
            if pay >= threshold:
                above_threshold.append((internship, f"${pay}/hr"))
            else:
                below_threshold.append((internship, f"${pay}/hr"))
        else:
            not_found.append(internship)
    
    return above_threshold, below_threshold, not_found

# Main Streamlit app
def main():
    st.title("Internship Salary Filter")
    
    # Sidebar to specify the pay threshold
    st.sidebar.title("Settings")
    threshold = st.sidebar.slider(
        "Set Pay Threshold ($/hr)",
        min_value=0,
        max_value=200,
        value=50,
        step=5
    )
    
    # File path for Excel data
    excel_file = "levels_data.xlsx"

    # Read the Excel data
    excel_data = read_excel_data(excel_file)
    if excel_data.empty:
        st.error("No valid data found in the Excel file.")
        return

    # Calculate and display the percentage of companies above the threshold
    percentage_above_threshold = calculate_threshold_percentage(excel_data, threshold)
    st.sidebar.write(f"Your threshold is in the top {percentage_above_threshold:.2f}% of company pays on Levels.fyi.")

    # User input for internship list
    internship_input = st.text_area(
        "Enter Internship Company Names and Info (One per line)",
        height=200,
        placeholder="Radix Trading\nDE.. Shaw - with Fuzzy Match\nVirtu Financial - Summer 2025 Internship\nAmazon - Quantitative Researcher\nHoneywell - Quantitative Researcher\nSpectrum - CEO - Intern\nSomos Inc. - Software Engineer Intern"
    )

    if st.button("Check Salaries"):
        if not internship_input.strip():
            st.warning("Please enter internship company names.")
            return
        
        # Split user input into a list of company names
        internships = internship_input.strip().split('\n')

        # Categorize internships based on user-defined threshold
        above_threshold, below_threshold, not_found = categorize_internships(internships, excel_data, threshold)

        # Display results
        st.subheader(f"Internships That Pay Above Your Threshold (${threshold}/hr):")
        if above_threshold:
            above_df = pd.DataFrame(above_threshold, columns=["Company Info", "Hourly Pay"])
            st.dataframe(above_df)
        else:
            st.info(f"No internships found that meet the pay threshold of ${threshold}/hr.")

        st.subheader(f"Internships That Pay Below Your Threshold (${threshold}/hr):")
        if below_threshold:
            below_df = pd.DataFrame(below_threshold, columns=["Company Info", "Hourly Pay"])
            st.dataframe(below_df)
        else:
            st.info(f"No internships found that pay below the threshold of ${threshold}/hr.")

        st.subheader("Internships That We Couldn't Find Data For:")
        if not_found:
            not_found_df = pd.DataFrame(not_found, columns=["Company Info"])
            st.dataframe(not_found_df)
        else:
            st.info("All internships were found in the data.")

if __name__ == "__main__":
    main()
