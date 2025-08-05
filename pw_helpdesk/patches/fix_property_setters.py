import frappe

def execute():
    """
    Fix Property Setters that are missing doc_type field
    """
    try:
        # Fix Property Setters without doc_type
        property_setters = frappe.db.sql("""
            SELECT name, doctype_or_field, field_name, property
            FROM `tabProperty Setter`
            WHERE doc_type IS NULL OR doc_type = ''
        """, as_dict=True)
        
        for ps in property_setters:
            try:
                # Try to determine the doc_type from the name pattern
                if ps.get('name'):
                    name_parts = ps['name'].split('-')
                    if len(name_parts) >= 2:
                        potential_doctype = name_parts[0]
                        
                        # Validate if this is actually a doctype
                        if frappe.db.exists("DocType", potential_doctype):
                            frappe.db.sql("""
                                UPDATE `tabProperty Setter`
                                SET doc_type = %s
                                WHERE name = %s
                            """, (potential_doctype, ps['name']))
                            print(f"Fixed Property Setter: {ps['name']} -> doc_type: {potential_doctype}")
                        else:
                            # If we can't determine the doctype, delete the broken property setter
                            frappe.db.sql("DELETE FROM `tabProperty Setter` WHERE name = %s", ps['name'])
                            print(f"Deleted broken Property Setter: {ps['name']}")
                    else:
                        # Delete property setters with invalid names
                        frappe.db.sql("DELETE FROM `tabProperty Setter` WHERE name = %s", ps['name'])
                        print(f"Deleted Property Setter with invalid name: {ps['name']}")
            except Exception as e:
                print(f"Error fixing Property Setter {ps.get('name', 'Unknown')}: {str(e)}")
                # Delete the problematic property setter
                try:
                    frappe.db.sql("DELETE FROM `tabProperty Setter` WHERE name = %s", ps['name'])
                    print(f"Deleted problematic Property Setter: {ps['name']}")
                except:
                    pass
        
        frappe.db.commit()
        print("Property Setter fix completed successfully")
        
    except Exception as e:
        print(f"Error in Property Setter fix: {str(e)}")
        frappe.db.rollback() 