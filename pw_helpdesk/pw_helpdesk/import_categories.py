#!/usr/bin/env python3
"""
Script to import HD Categories and Sub Categories from CSV file
"""

import frappe
import csv
import os
from frappe import _

def import_categories_from_csv():
    """Import categories and sub-categories from CSV file"""
    
    # Path to the CSV file
    csv_file_path = '/Users/pavankumarmarwaha/Desktop/bench9/Entities - PhysicsWallah - Helpdesk Categories.csv'
    
    if not os.path.exists(csv_file_path):
        frappe.throw(f"CSV file not found at: {csv_file_path}")
    
    # Dictionary to store categories and their sub-categories
    categories = {}
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Debug: Print column names
            print(f"CSV columns: {reader.fieldnames}")
            
            row_count = 0
            for row in reader:
                row_count += 1
                
                category_name = row.get('Category Name', '').strip()
                category_code = row.get('Category Code', '').strip()
                sub_category_name = row.get('Sub-Category Name', '').strip()
                sub_category_code = row.get('Sub-Category Code', '').strip()
                description = row.get('Description', '').strip()
                
                # Skip completely empty rows
                if not category_name and not sub_category_name:
                    continue
                
                # If this is a main category row (has category name and code)
                if category_name and category_code:
                    if category_name not in categories:
                        categories[category_name] = {
                            'category_code': category_code,
                            'description': description,
                            'sub_categories': []
                        }
                        print(f"Added main category: {category_name}")
                
                # If this is a sub-category row (has sub-category name and code)
                elif sub_category_name and sub_category_code:
                    # Find the parent category by looking at the sub-category code pattern
                    # Most sub-category codes start with "SUB_" followed by a prefix that matches the parent category
                    parent_category = None
                    
                    # Try to find parent category by matching sub-category code patterns
                    for cat_name, cat_data in categories.items():
                        if cat_data['category_code'] in sub_category_code or sub_category_code.startswith('SUB_'):
                            parent_category = cat_name
                            break
                    
                    # If no parent found, create a default parent category
                    if not parent_category:
                        parent_category = "General"
                        if parent_category not in categories:
                            categories[parent_category] = {
                                'category_code': 'GEN',
                                'description': 'General category for orphaned sub-categories',
                                'sub_categories': []
                            }
                    
                    # Add sub-category to the parent
                    categories[parent_category]['sub_categories'].append({
                        'sub_category_name': sub_category_name,
                        'sub_category_code': sub_category_code,
                        'description': description,
                        'same_assignee_as_category': row.get('Same Assignee as Category', '').strip() == 'Yes',
                        'assign_issue_to_user': row.get('Assign Issue To User', '').strip() == 'Yes',
                        'assignee': row.get('Assignee', '').strip(),
                        'assign_issue_to_external_vendor': row.get('Assign Issue to External Vendor', '').strip() == 'Yes',
                        'assign_issue_to_permission_role_holder': row.get('Assign Issue to Permission Role Holder', '').strip() == 'Yes',
                        'permission_role_holder': row.get('Permission Role Holder', '').strip(),
                        'attach_form_for_issue_creation': row.get('Attach Form for Issue Creation', '').strip() == 'Yes',
                        'attach_same_form_as_category': row.get('Attach same form as Category', '').strip() == 'Yes',
                        'make_attachment_mandatory': row.get('Make Attachment Mandatory', '').strip() == 'Yes',
                        'same_attachment_setting_as_category': row.get('Same Attachment Setting as Category', '').strip() == 'Yes',
                        'hide_attachment_field': row.get('Hide Attachment Field', '').strip() == 'Yes',
                        'display_sub_category_only_in_mobile_app': row.get('Display Sub-Category only in Mobile App', '').strip() == 'Yes',
                        'make_location_mandatory': row.get('Make Location Mandatory', '').strip() == 'Yes',
                        'same_escalation_settings_as_category': row.get('Same Escalation Settings as Category', '').strip() == 'Yes',
                        'enable_escalation': row.get('Enable Escalation', '').strip() == 'Yes',
                        'escalation_type': row.get('Escalation Type', '').strip(),
                        'escalation_1_point': int(row.get('Escalation 1 Point', 0)) if row.get('Escalation 1 Point', '').strip() else None,
                        'escalation_1_unit': row.get('Escalation 1 Unit', '').strip(),
                        'escalation_1_assignee': row.get('Escalation 1 Assignee', '').strip(),
                        'escalation_2_point': int(row.get('Escalation 2 Point', 0)) if row.get('Escalation 2 Point', '').strip() else None,
                        'escalation_2_unit': row.get('Escalation 2 Unit', '').strip(),
                        'escalation_2_assignee': row.get('Escalation 2 Assignee', '').strip(),
                        'escalation_3_point': int(row.get('Escalation 3 Point', 0)) if row.get('Escalation 3 Point', '').strip() else None,
                        'escalation_3_unit': row.get('Escalation 3 Unit', '').strip(),
                        'escalation_3_assignee': row.get('Escalation 3 Assignee', '').strip()
                    })
                    print(f"Added sub-category: {sub_category_name} to parent: {parent_category}")
        
        print(f"Parsed {len(categories)} categories from CSV")
        
        # Create categories and sub-categories
        created_categories = 0
        created_sub_categories = 0
        
        for category_name, category_data in categories.items():
            try:
                # Check if category already exists
                existing_category = frappe.get_all(
                    "HD Category",
                    filters={"category_name": category_name},
                    limit=1
                )
                
                if existing_category:
                    print(f"Category '{category_name}' already exists, skipping...")
                    continue
                
                # Create category
                category_doc = frappe.get_doc({
                    "doctype": "HD Category",
                    "category_name": category_name,
                    "category_code": category_data['category_code'],
                    "description": category_data['description'],
                    "is_active": 1
                })
                category_doc.insert()
                created_categories += 1
                print(f"Created category: {category_name}")
                
                # Create sub-categories
                for sub_cat_data in category_data['sub_categories']:
                    try:
                        # Check if sub-category already exists
                        existing_sub_category = frappe.get_all(
                            "HD Category",
                            filters={"category_code": sub_cat_data['sub_category_code']},
                            limit=1
                        )
                        
                        if existing_sub_category:
                            print(f"Sub-category '{sub_cat_data['sub_category_name']}' already exists, skipping...")
                            continue
                        
                        # Create sub-category
                        sub_category_doc = frappe.get_doc({
                            "doctype": "HD Category",
                            "is_sub_category": 1,
                            "parent_category": category_doc.name,
                            "category_name": sub_cat_data['sub_category_name'],
                            "category_code": sub_cat_data['sub_category_code'],
                            "description": sub_cat_data['description'],
                            "is_active": 1,
                            "same_assignee_as_category": sub_cat_data['same_assignee_as_category'],
                            "assign_issue_to_user": sub_cat_data['assign_issue_to_user'],
                            "assignee": sub_cat_data['assignee'],
                            "assign_issue_to_external_vendor": sub_cat_data['assign_issue_to_external_vendor'],
                            "assign_issue_to_permission_role_holder": sub_cat_data['assign_issue_to_permission_role_holder'],
                            "permission_role_holder": sub_cat_data['permission_role_holder'],
                            "attach_form_for_issue_creation": sub_cat_data['attach_form_for_issue_creation'],
                            "attach_same_form_as_category": sub_cat_data['attach_same_form_as_category'],
                            "make_attachment_mandatory": sub_cat_data['make_attachment_mandatory'],
                            "same_attachment_setting_as_category": sub_cat_data['same_attachment_setting_as_category'],
                            "hide_attachment_field": sub_cat_data['hide_attachment_field'],
                            "display_sub_category_only_in_mobile_app": sub_cat_data['display_sub_category_only_in_mobile_app'],
                            "make_location_mandatory": sub_cat_data['make_location_mandatory'],
                            "same_escalation_settings_as_category": sub_cat_data['same_escalation_settings_as_category'],
                            "enable_escalation": sub_cat_data['enable_escalation'],
                            "escalation_type": sub_cat_data['escalation_type'],
                            "escalation_1_point": sub_cat_data['escalation_1_point'],
                            "escalation_1_unit": sub_cat_data['escalation_1_unit'],
                            "escalation_1_assignee": sub_cat_data['escalation_1_assignee'],
                            "escalation_2_point": sub_cat_data['escalation_2_point'],
                            "escalation_2_unit": sub_cat_data['escalation_2_unit'],
                            "escalation_2_assignee": sub_cat_data['escalation_2_assignee'],
                            "escalation_3_point": sub_cat_data['escalation_3_point'],
                            "escalation_3_unit": sub_cat_data['escalation_3_unit'],
                            "escalation_3_assignee": sub_cat_data['escalation_3_assignee']
                        })
                        sub_category_doc.insert()
                        created_sub_categories += 1
                        print(f"  Created sub-category: {sub_cat_data['sub_category_name']}")
                        
                    except Exception as e:
                        print(f"Error creating sub-category '{sub_cat_data['sub_category_name']}': {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Error creating category '{category_name}': {str(e)}")
                continue
        
        print(f"\nImport completed!")
        print(f"Created {created_categories} categories")
        print(f"Created {created_sub_categories} sub-categories")
        
    except Exception as e:
        frappe.throw(f"Error reading CSV file: {str(e)}")

if __name__ == "__main__":
    import_categories_from_csv() 