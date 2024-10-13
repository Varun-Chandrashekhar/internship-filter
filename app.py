import streamlit as st
import pandas as pd
import re
from fuzzywuzzy import process

st.title("Internship Filter")

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

# Function to match based on the first word and choose the highest-paying match
def match_highest_paying_company(company_name, excel_data, threshold=80):
    cleaned_name = clean_company_name(company_name)
    
    # Fuzzy matching for potential matches
    choices = excel_data['Company'].apply(clean_company_name).tolist()
    matches = process.extract(cleaned_name, choices, limit=len(choices))
    
    # Filter matches based on the fuzzy threshold score
    valid_matches = [match for match in matches if match[1] >= threshold]
    
    if valid_matches:
        # Filter the data to get rows that match the valid matches
        matched_rows = excel_data[excel_data['Company'].apply(clean_company_name).isin([match[0] for match in valid_matches])]
        # Return the row with the highest pay
        return matched_rows.loc[matched_rows['Hourly Salary'].idxmax()]
    return None

# Function to calculate what percentage of companies are below the threshold
def calculate_threshold_percentage(excel_data, threshold):
    total_companies = len(excel_data)
    below_threshold = len(excel_data[excel_data['Hourly Salary'] < threshold])
    percentage = (below_threshold / total_companies) * 100
    return 100 - percentage  # Percentage above the threshold

# Function to categorize internships based on pay using fuzzy matching
def categorize_internships(internships, excel_data, threshold=50, fuzzy_threshold=90):
    above_threshold = []
    below_threshold = []
    not_found = []
    
    for internship in internships:
        company_name = extract_company_name(internship)
        matched_row = match_highest_paying_company(company_name, excel_data, fuzzy_threshold)
        
        if matched_row is not None:
            pay = matched_row['Hourly Salary']
            if pay >= threshold:
                above_threshold.append((internship, f"${pay}/hr"))
            else:
                below_threshold.append((internship, f"${pay}/hr"))
        else:
            not_found.append(internship)
    
    # Sort above and below threshold data by pay in descending order
    above_threshold.sort(key=lambda x: float(x[1].replace("$", "").replace("/hr", "")), reverse=True)
    below_threshold.sort(key=lambda x: float(x[1].replace("$", "").replace("/hr", "")), reverse=True)
    
    return above_threshold, below_threshold, not_found

# Function to check for duplicates with previously applied internships
def check_already_applied(new_internships, applied_internships, fuzzy_threshold=95):
    already_applied = []
    
    for new_internship in new_internships:
        best_match, score = process.extractOne(new_internship, applied_internships)
        if score >= fuzzy_threshold:
            already_applied.append((new_internship, best_match, score))
    
    return already_applied

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
else:
    # Calculate and display the percentage of companies above the threshold
    percentage_above_threshold = calculate_threshold_percentage(excel_data, threshold)
    st.sidebar.write(f"Your threshold is in the top {percentage_above_threshold:.2f}% of company pays on Levels.fyi.")
    
    # Display Levels data in the sidebar
    st.sidebar.subheader("Levels.fyi Company Data:")
    st.sidebar.dataframe(excel_data)
    
    # Links for additional resources
    st.sidebar.subheader("Useful Links:")
    st.sidebar.markdown("[Internship Tracker](https://docs.google.com/spreadsheets/d/1tlUVgtnJBWpaaiLY-QeU8A8gMVolEGyQl6fRaUqpptg/edit?usp=sharing)")
    st.sidebar.markdown("[Pit CSC GitHub Repo](https://github.com/SimplifyJobs/Summer2025-Internships)")
    st.sidebar.markdown("[Ouckah GitHub Repo](https://github.com/Ouckah/Summer2025-Internships)")
    
    # Input for internships the user has already applied to
    applied_internships_input = st.text_area(
        "Paste the internships you've already applied to:",
        height=150,
        placeholder="Radix Trading - Summer 2025\nGoogle - SWE Intern\n..."
    )
    
    applied_internships = applied_internships_input.strip().split('\n') if applied_internships_input else []
    
    # User input for internship list
    internship_input = st.text_area(
        "Enter Internship Company Names and Info (One per line)",
        height=200,
        placeholder="Radix Trading\nDE.. Shaw - with Fuzzy Match\nVirtu Financial - Summer 2025 Internship\nAmazon - Quantitative Researcher\nHoneywell - Quantitative Researcher\nSpectrum - CEO - Intern\nSomos Inc. - Software Engineer Intern"
    )

    if st.button("Check Salaries"):
        if not internship_input.strip():
            st.warning("Please enter internship company names.")
        else:
            # Split user input into a list of company names
            internships = internship_input.strip().split('\n')

            # Check for already applied internships based on fuzzy matching
            already_applied_matches = check_already_applied(internships, applied_internships)
            
            # Prepare list for already applied internships with pay info, matched name, and score
            already_applied_with_details = []
            matched_applied_internships = []  # To keep track for exclusion
            
            for new_internship, matched_applied, score in already_applied_matches:
                company_name = extract_company_name(new_internship)
                matched_row = match_highest_paying_company(company_name, excel_data, threshold=80)
                if matched_row is not None:
                    pay = matched_row['Hourly Salary']
                else:
                    pay = 0  # Default pay if not found
                already_applied_with_details.append({
                    "Internship Info": new_internship,
                    "Matched Applied Internship": matched_applied,
                    "Fuzzy Match Score": score,
                    "Hourly Pay": f"${pay}/hr" if pay > 0 else "$0/hr"
                })
                matched_applied_internships.append(new_internship)
            
            # Remove already applied internships from the main internships list
            remaining_internships = [i for i in internships if i not in matched_applied_internships]
            
            # Categorize remaining internships based on user-defined threshold
            above_threshold, below_threshold, not_found = categorize_internships(remaining_internships, excel_data, threshold)
            
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
    
            # Display Already Applied Internships with Pay Information, Matched Name, and Score
            if already_applied_with_details:
                st.subheader("You Have Already Applied To:")
                already_applied_df = pd.DataFrame(already_applied_with_details)
                st.dataframe(already_applied_df)
            else:
                st.info("No duplicate applications found.")
    
            # Combine all tables into one complete table to display
            st.subheader("Complete Combined Table:")
    
            # Adding a column to indicate the category
            combined_above = pd.DataFrame(above_threshold, columns=["Company Info", "Hourly Pay"])
            combined_above['Category'] = 'Above Threshold'
            
            combined_below = pd.DataFrame(below_threshold, columns=["Company Info", "Hourly Pay"])
            combined_below['Category'] = 'Below Threshold'
            
            combined_not_found = pd.DataFrame(not_found, columns=["Company Info"])
            combined_not_found['Hourly Pay'] = 'N/A'
            combined_not_found['Category'] = 'Not Found'
            
            # Prepare the Already Applied data with additional details
            combined_applied = pd.DataFrame(already_applied_with_details)
            combined_applied.rename(columns={
                "Internship Info": "Company Info",
                "Matched Applied Internship": "Matched Applied Internship",
                "Fuzzy Match Score": "Fuzzy Match Score",
                "Hourly Pay": "Hourly Pay"
            }, inplace=True)
            combined_applied['Category'] = 'Already Applied'
            
            # For consistency, ensure all dataframes have the same columns
            # Add missing columns to combined_above, combined_below, combined_not_found
            combined_above['Matched Applied Internship'] = ''
            combined_above['Fuzzy Match Score'] = ''
            
            combined_below['Matched Applied Internship'] = ''
            combined_below['Fuzzy Match Score'] = ''
            
            combined_not_found['Matched Applied Internship'] = ''
            combined_not_found['Fuzzy Match Score'] = ''
            
            # Reorder columns to match
            combined_above = combined_above[['Company Info', 'Hourly Pay', 'Matched Applied Internship', 'Fuzzy Match Score', 'Category']]
            combined_below = combined_below[['Company Info', 'Hourly Pay', 'Matched Applied Internship', 'Fuzzy Match Score', 'Category']]
            combined_not_found = combined_not_found[['Company Info', 'Hourly Pay', 'Matched Applied Internship', 'Fuzzy Match Score', 'Category']]
            combined_applied = combined_applied[['Company Info', 'Hourly Pay', 'Matched Applied Internship', 'Fuzzy Match Score', 'Category']]
            
            # Concatenate all dataframes
            combined_table = pd.concat([combined_above, combined_below, combined_not_found, combined_applied], ignore_index=True)
            
            # Rearrange columns for better readability
            combined_table = combined_table[['Company Info', 'Hourly Pay', 'Matched Applied Internship', 'Fuzzy Match Score', 'Category']]
            
            st.dataframe(combined_table)
