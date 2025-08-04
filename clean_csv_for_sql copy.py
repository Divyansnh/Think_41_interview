#!/usr/bin/env python3
"""
Script to clean CSV file for SQL Workbench import by removing non-ASCII characters
"""

import csv
import sys
import os

def clean_csv_for_sql(input_file, output_file):
    """
    Clean CSV file by removing or replacing non-ASCII characters
    """
    print(f"Cleaning {input_file}...")
    
    rows_processed = 0
    chars_replaced = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile, \
             open(output_file, 'w', encoding='ascii', errors='ignore', newline='') as outfile:
            
            # Read the entire content and replace problematic characters
            content = infile.read()
            
            # Replace common UTF-8 characters with ASCII equivalents
            replacements = {
                'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ã': 'a', 'å': 'a',
                'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
                'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i',
                'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'õ': 'o',
                'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u',
                'ñ': 'n', 'ç': 'c',
                'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ã': 'A', 'Å': 'A',
                'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E',
                'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I',
                'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O', 'Õ': 'O',
                'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U',
                'Ñ': 'N', 'Ç': 'C',
                '"': '"', '"': '"', ''': "'", ''': "'",
                '–': '-', '—': '-', '…': '...'
            }
            
            # Apply replacements
            for utf_char, ascii_char in replacements.items():
                if utf_char in content:
                    chars_replaced += content.count(utf_char)
                    content = content.replace(utf_char, ascii_char)
            
            # Write cleaned content
            outfile.write(content)
            
            # Count rows
            rows_processed = content.count('\n')
            
        print(f"✅ Successfully cleaned CSV file!")
        print(f"   - Rows processed: {rows_processed}")
        print(f"   - Characters replaced: {chars_replaced}")
        print(f"   - Output file: {output_file}")
        
    except Exception as e:
        print(f"❌ Error cleaning CSV file: {e}")
        return False
    
    return True

def main():
    input_file = "/Users/divyanshsingh/Downloads/archive/users_cleaned.csv"
    output_file = "/Users/divyanshsingh/Downloads/archive/users_cleaned_ascii.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    print("🧹 CSV Cleaner for SQL Workbench")
    print("=" * 40)
    
    if clean_csv_for_sql(input_file, output_file):
        print(f"\n📁 Use this file in SQL Workbench: {output_file}")
        print("\n💡 Import Tips:")
        print("   1. Use the new ASCII file for import")
        print("   2. Set encoding to 'ASCII' or 'UTF-8' in SQL Workbench")
        print("   3. Make sure field separator is set to comma (,)")
    else:
        print("\n❌ Failed to clean the CSV file")

if __name__ == "__main__":
    main()
