import frappe
from frappe import _


def on_ticket_comment_insert(doc, method):
    """Auto-update ticket status when agent responds for the first time"""
    if not doc.ticket:
        return
        
    ticket = frappe.get_doc("HD Ticket", doc.ticket)
    
    # Check if the commenter is an agent (not the ticket raiser)
    if doc.commented_by != ticket.raised_by:
        # Check if this is the first agent response
        if ticket.status == "Open" and not ticket.first_responded_on:
            ticket.status = "Replied"
            ticket.first_responded_on = frappe.utils.now_datetime()
            ticket.save(ignore_permissions=True)


def validate_ticket_closure(doc, method):
    """Validate ticket closure permissions"""
    if not doc.is_new() and doc.status == "Closed":
        old_doc = doc.get_doc_before_save()
        if old_doc and old_doc.status != "Closed":
            current_user = frappe.session.user
            
            # Allow if user is System Manager or ticket raiser
            if "System Manager" in frappe.get_roles(current_user) or current_user == doc.raised_by:
                return
                
            frappe.throw(_("Only the person who raised the ticket or a System Manager can close this ticket."))


def auto_assign_based_on_category(doc, method):
    """Auto-assign ticket based on category"""
    if doc.custom_category:
        try:
            category_doc = frappe.get_doc("HD Category", doc.custom_category)
            
            # Set agent group
            team_mapping = {
                "Technical Support": "Technical Support Team",
                "Billing": "Billing Support Team"
            }
            
            if category_doc.category_name in team_mapping:
                team_name = team_mapping[category_doc.category_name]
                if frappe.db.exists("HD Team", team_name):
                    doc.agent_group = team_name
                    
        except Exception as e:
            frappe.log_error(f"Error in category assignment: {str(e)}") 