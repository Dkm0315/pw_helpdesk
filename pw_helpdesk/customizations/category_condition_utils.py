import frappe
from frappe import _


class CategoryConditionGenerator:
    """Utility class to convert user-friendly category selections to Python conditions"""
    
    @staticmethod
    def generate_condition_from_categories(categories):
        """
        Convert list of categories to Python condition expression
        
        Args:
            categories: List of category names
            
        Returns:
            str: Python condition expression for Frappe's safe_eval
        """
        if not categories:
            return None
            
        # Remove duplicates and empty values
        unique_categories = list(set([cat for cat in categories if cat]))
        
        if not unique_categories:
            return None
            
        if len(unique_categories) == 1:
            return f"doc.custom_category == '{unique_categories[0]}'"
        else:
            category_list = "', '".join(unique_categories)
            return f"doc.custom_category in ['{category_list}']"
    
    @staticmethod
    def update_sla_condition_from_categories(sla_doc):
        """
        Update SLA condition based on selected categories
        
        Args:
            sla_doc: HD Service Level Agreement document
        """
        try:
            if not hasattr(sla_doc, 'custom_applicable_categories'):
                return
                
            categories = []
            for row in sla_doc.custom_applicable_categories or []:
                if row.category:
                    categories.append(row.category)
            
            condition = CategoryConditionGenerator.generate_condition_from_categories(categories)
            
            if condition:
                sla_doc.condition = condition
                frappe.msgprint(f"Condition auto-generated: {condition}")
            else:
                sla_doc.condition = None
                frappe.msgprint("No categories selected, condition cleared")
                
        except Exception as e:
            frappe.log_error(f"Error generating SLA condition: {str(e)}")
            frappe.throw(_("Error generating condition: {0}").format(str(e)))
    
    @staticmethod
    def update_assignment_rule_condition_from_categories(assignment_rule_doc):
        """
        Update Assignment Rule condition based on selected categories
        
        Args:
            assignment_rule_doc: Assignment Rule document
        """
        try:
            if not hasattr(assignment_rule_doc, 'custom_applicable_categories'):
                return
                
            categories = []
            for row in assignment_rule_doc.custom_applicable_categories or []:
                if row.category:
                    categories.append(row.category)
            
            # For assignment rules, we need to include the HD Ticket check
            base_condition = CategoryConditionGenerator.generate_condition_from_categories(categories)
            
            if base_condition:
                # Assignment rules work with different variable names
                assignment_condition = base_condition.replace('doc.custom_category', 'custom_category')
                assignment_rule_doc.assign_condition = assignment_condition
                frappe.msgprint(f"Assignment condition auto-generated: {assignment_condition}")
            else:
                frappe.msgprint("No categories selected, assignment condition not modified")
                
        except Exception as e:
            frappe.log_error(f"Error generating assignment rule condition: {str(e)}")
            frappe.throw(_("Error generating assignment condition: {0}").format(str(e)))
    
    @staticmethod
    def migrate_existing_conditions_to_categories(doctype):
        """
        Reverse migration: Extract categories from existing conditions and populate the multiselect
        
        Args:
            doctype: "HD Service Level Agreement" or "Assignment Rule"
        """
        try:
            condition_field = "condition" if doctype == "HD Service Level Agreement" else "assign_condition"
            
            docs = frappe.get_all(doctype, 
                filters={condition_field: ["is", "set"]},
                fields=["name", condition_field])
            
            for doc_info in docs:
                doc = frappe.get_doc(doctype, doc_info.name)
                condition = getattr(doc, condition_field, None)
                
                if condition:
                    categories = CategoryConditionGenerator.extract_categories_from_condition(condition)
                    if categories:
                        # Clear existing category selections
                        doc.custom_applicable_categories = []
                        
                        # Add extracted categories
                        for category in categories:
                            if frappe.db.exists("HD Category", category):
                                doc.append("custom_applicable_categories", {"category": category})
                        
                        doc.save(ignore_permissions=True)
                        print(f"Migrated {doctype} '{doc.name}': {categories}")
                        
        except Exception as e:
            frappe.log_error(f"Error migrating {doctype} conditions: {str(e)}")
            print(f"Error migrating {doctype}: {str(e)}")
    
    @staticmethod
    def extract_categories_from_condition(condition):
        """
        Extract category names from Python condition expressions
        
        Args:
            condition: Python condition string
            
        Returns:
            list: List of category names
        """
        try:
            categories = []
            
            if not condition:
                return categories
                
            # Handle single category: doc.custom_category == 'AI_AM_1'
            if "==" in condition and "custom_category" in condition:
                import re
                match = re.search(r"custom_category\s*==\s*['\"]([^'\"]+)['\"]", condition)
                if match:
                    categories.append(match.group(1))
            
            # Handle multiple categories: doc.custom_category in ['AI_AM_1', 'AI_AM_2']
            elif " in " in condition and "custom_category" in condition:
                import re
                matches = re.findall(r"['\"]([^'\"]+)['\"]", condition)
                categories.extend(matches)
            
            return list(set(categories))  # Remove duplicates
            
        except Exception as e:
            frappe.log_error(f"Error extracting categories from condition: {str(e)}")
            return []


@frappe.whitelist()
def auto_generate_sla_condition(sla_name):
    """
    Whitelisted method to auto-generate SLA condition from categories
    
    Args:
        sla_name: Name of the HD Service Level Agreement
    """
    try:
        sla_doc = frappe.get_doc("HD Service Level Agreement", sla_name)
        CategoryConditionGenerator.update_sla_condition_from_categories(sla_doc)
        sla_doc.save(ignore_permissions=True)
        return {"success": True, "condition": sla_doc.condition}
    except Exception as e:
        frappe.log_error(f"Error in auto_generate_sla_condition: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def auto_generate_assignment_rule_condition(rule_name):
    """
    Whitelisted method to auto-generate Assignment Rule condition from categories
    
    Args:
        rule_name: Name of the Assignment Rule
    """
    try:
        rule_doc = frappe.get_doc("Assignment Rule", rule_name)
        CategoryConditionGenerator.update_assignment_rule_condition_from_categories(rule_doc)
        rule_doc.save(ignore_permissions=True)
        return {"success": True, "condition": rule_doc.assign_condition}
    except Exception as e:
        frappe.log_error(f"Error in auto_generate_assignment_rule_condition: {str(e)}")
        return {"success": False, "error": str(e)} 