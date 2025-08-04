import frappe
from frappe import _
import json

@frappe.whitelist()
def get_applicable_sla(category):
    """Get applicable SLA for a given category"""
    try:
        if not category:
            return {"sla": None}
            
        # Find SLA agreements that include this category
        sla_data = frappe.db.sql("""
            SELECT DISTINCT 
                sla.name as sla_name,
                sla.custom_auto_assign_team,
                sla.custom_assignment_rule,
                sla.default_service_level_agreement
            FROM `tabHD Category MultiSelect` cms
            JOIN `tabHD Service Level Agreement` sla ON cms.parent = sla.name
            WHERE cms.category = %s AND sla.enabled = 1
            ORDER BY sla.default_service_level_agreement DESC, sla.creation ASC
            LIMIT 1
        """, (category,), as_dict=True)
        
        if sla_data:
            sla_agreement = sla_data[0]
            return {
                "sla": sla_agreement.sla_name,
                "sla_name": sla_agreement.sla_name,
                "team": sla_agreement.custom_auto_assign_team,
                "assignment_rule": sla_agreement.custom_assignment_rule
            }
        else:
            return {"sla": None}
            
    except Exception as e:
        frappe.log_error(f"Error getting applicable SLA: {str(e)}", "SLA API Error")
        return {"sla": None}

@frappe.whitelist()
def check_sla_status(ticket_id, category=None):
    """Check SLA status for a ticket"""
    try:
        ticket = frappe.get_doc("HD Ticket", ticket_id)
        
        if not ticket.sla:
            if category:
                applicable_sla = get_applicable_sla(category)
                if applicable_sla.get("sla"):
                    return f"No SLA currently applied. Suggested SLA for category '{category}': {applicable_sla['sla_name']}"
                else:
                    return f"No SLA found for category '{category}'"
            else:
                return "No SLA applied to this ticket"
        
        sla_doc = frappe.get_doc("HD Service Level Agreement", ticket.sla)
        
        status_info = []
        status_info.append(f"Current SLA: {sla_doc.name}")
        
        if ticket.response_by:
            if frappe.utils.now_datetime() > ticket.response_by:
                status_info.append("⚠️ Response time exceeded")
            else:
                time_left = frappe.utils.time_diff_in_hours(ticket.response_by, frappe.utils.now_datetime())
                status_info.append(f"Response due in {time_left:.1f} hours")
        
        if ticket.resolution_by:
            if frappe.utils.now_datetime() > ticket.resolution_by:
                status_info.append("⚠️ Resolution time exceeded")
            else:
                time_left = frappe.utils.time_diff_in_hours(ticket.resolution_by, frappe.utils.now_datetime())
                status_info.append(f"Resolution due in {time_left:.1f} hours")
        
        return " | ".join(status_info)
        
    except Exception as e:
        frappe.log_error(f"Error checking SLA status: {str(e)}", "SLA Status Check Error")
        return "Error checking SLA status"

@frappe.whitelist()
def apply_sla_to_ticket(ticket_id, sla_name):
    """Manually apply SLA to a ticket"""
    try:
        ticket = frappe.get_doc("HD Ticket", ticket_id)
        
        if not frappe.db.exists("HD Service Level Agreement", sla_name):
            frappe.throw(_("SLA not found"))
        
        ticket.sla = sla_name
        ticket.save(ignore_permissions=True)
        
        # Get SLA details for team assignment
        sla_doc = frappe.get_doc("HD Service Level Agreement", sla_name)
        if hasattr(sla_doc, 'custom_auto_assign_team') and sla_doc.custom_auto_assign_team:
            ticket.agent_group = sla_doc.custom_auto_assign_team
            ticket.save(ignore_permissions=True)
        
        return f"SLA '{sla_name}' applied successfully"
        
    except Exception as e:
        frappe.log_error(f"Error applying SLA: {str(e)}", "SLA Application Error")
        frappe.throw(_("Failed to apply SLA"))

@frappe.whitelist()
def get_sla_categories(sla_name):
    """Get categories associated with an SLA"""
    try:
        categories = frappe.db.sql("""
            SELECT category
            FROM `tabHD Category MultiSelect`
            WHERE parent = %s
        """, (sla_name,), as_dict=True)
        
        return [cat.category for cat in categories]
        
    except Exception as e:
        frappe.log_error(f"Error getting SLA categories: {str(e)}", "SLA Categories Error")
        return []

@frappe.whitelist()
def update_sla_categories(sla_name, categories):
    """Update categories for an SLA"""
    try:
        if isinstance(categories, str):
            categories = json.loads(categories)
            
        sla_doc = frappe.get_doc("HD Service Level Agreement", sla_name)
        
        # Clear existing categories
        sla_doc.custom_applicable_categories = []
        
        # Add new categories
        for category in categories:
            sla_doc.append("custom_applicable_categories", {
                "category": category
            })
        
        sla_doc.save(ignore_permissions=True)
        
        return f"Categories updated for SLA '{sla_name}'"
        
    except Exception as e:
        frappe.log_error(f"Error updating SLA categories: {str(e)}", "SLA Categories Update Error")
        frappe.throw(_("Failed to update SLA categories")) 