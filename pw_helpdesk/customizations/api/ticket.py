import frappe
from frappe import _


@frappe.whitelist()
def request_closure(ticket_id, resolution_notes):
    """
    API endpoint to request ticket closure by agents.
    Only agents can request closure, but only ticket raiser and System Managers can actually close it.
    """
    
    # Check if the ticket exists
    if not frappe.db.exists("HD Ticket", ticket_id):
        frappe.throw(_("Ticket not found"))
    
    # Get the ticket
    ticket = frappe.get_doc("HD Ticket", ticket_id)
    
    # Check if user has permission to request closure (is an agent)
    if not frappe.has_permission("HD Ticket", "write", doc=ticket):
        frappe.throw(_("You don't have permission to request closure for this ticket"))
    
    # Check if ticket is already closed or resolved
    if ticket.status in ["Closed", "Resolved"]:
        frappe.throw(_("Ticket is already {0}").format(ticket.status))
    
    # Create a comment indicating closure request
    comment = frappe.get_doc({
        "doctype": "HD Ticket Comment",
        "ticket": ticket_id,
        "commented_by": frappe.session.user,
        "content": f"""
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <strong>🔔 Closure Requested by Agent</strong><br/>
            <strong>Resolution Notes:</strong><br/>
            {resolution_notes}
            <br/><br/>
            <em>This ticket has been marked for closure by the resolving agent. 
            The ticket can be closed by the person who raised it or by a System Manager.</em>
        </div>
        """,
        "is_system": 1
    }).insert()
    
    # Update custom fields to track closure request
    if hasattr(ticket, 'custom_closure_requested'):
        ticket.custom_closure_requested = 1
        ticket.custom_closure_requested_by = frappe.session.user
    
    # Add a comment to ticket activity
    ticket.add_comment("Info", f"Closure requested by {frappe.get_fullname(frappe.session.user)}: {resolution_notes}")
    
    ticket.save()
    
    # Send notification to ticket raiser
    if ticket.raised_by and ticket.raised_by != frappe.session.user:
        try:
            frappe.sendmail(
                recipients=[ticket.raised_by],
                subject=f"Closure Requested for Ticket #{ticket.name}",
                message=f"""
                <p>Hello,</p>
                <p>The agent working on your ticket <strong>#{ticket.name}</strong> has requested to close it.</p>
                <p><strong>Subject:</strong> {ticket.subject}</p>
                <p><strong>Resolution Notes:</strong></p>
                <p>{resolution_notes}</p>
                <p>If you are satisfied with the resolution, you can close the ticket. 
                Otherwise, please reply with additional questions or concerns.</p>
                <p>Best regards,<br/>Support Team</p>
                """
            )
        except Exception as e:
            frappe.log_error(f"Failed to send closure notification: {str(e)}")
    
    return {
        "message": "Closure request submitted successfully",
        "ticket_id": ticket_id,
        "status": ticket.status
    }


@frappe.whitelist()  
def auto_update_status_on_agent_reply(ticket_id):
    """
    Automatically update ticket status when agent replies for the first time
    """
    ticket = frappe.get_doc("HD Ticket", ticket_id)
    
    # Check if this is the first agent response
    if ticket.status == "Open" and not ticket.first_responded_on:
        ticket.status = "Replied"
        ticket.first_responded_on = frappe.utils.now_datetime()
        ticket.save()
        
        return {"message": "Status updated to Replied", "ticket_id": ticket_id}
    
    return {"message": "No status change needed"}


@frappe.whitelist()
def get_categories_by_parent(parent_category=None):
    """
    Get categories filtered by parent category for the form script
    """
    filters = {"is_active": 1}
    
    if parent_category:
        filters.update({
            "parent_category": parent_category,
            "is_sub_category": 1  
        })
    else:
        filters["is_sub_category"] = 0
        
    categories = frappe.get_all(
        "HD Category",
        filters=filters,
        fields=["name", "category_name", "category_code"],
        order_by="category_name asc"
    )
    
    return categories


@frappe.whitelist()
def assign_ticket_based_on_category(ticket_id, category):
    """
    Auto-assign ticket based on category settings
    """
    if not category:
        return {"message": "No category provided"}
        
    category_doc = frappe.get_doc("HD Category", category)
    ticket = frappe.get_doc("HD Ticket", ticket_id)
    
    # Check if category has assignment settings
    if category_doc.assign_issue_to_user and category_doc.assignee:
        # Assign to specific users
        assignees = [email.strip() for email in category_doc.assignee.split(",")]
        
        # Use frappe assignment
        for assignee in assignees[:1]:  # Assign to first user for now
            if frappe.db.exists("User", assignee):
                frappe.desk.form.assign_to.add({
                    "assign_to": [assignee],
                    "doctype": "HD Ticket", 
                    "name": ticket_id,
                    "description": f"Auto-assigned based on category: {category}"
                })
                break
                
    # Set agent group if team mapping exists
    team_mapping = {
        "Technical Support": "Technical Support Team",
        "Billing": "Billing Support Team"
    }
    
    if category_doc.category_name in team_mapping:
        team_name = team_mapping[category_doc.category_name]
        if frappe.db.exists("HD Team", team_name):
            ticket.agent_group = team_name
            ticket.save()
    
    return {"message": "Ticket assigned based on category", "ticket_id": ticket_id} 