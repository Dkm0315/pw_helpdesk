import frappe
from frappe import _
from frappe.utils import now, get_fullname


@frappe.whitelist()
def mark_as_resolved(**kwargs):
    """
    Mark ticket as resolved by the ticket raiser or system manager
    """
    # Get parameters from kwargs or form_dict
    ticket_id = kwargs.get('ticket_id') or frappe.form_dict.get('ticket_id')
    resolution_notes = kwargs.get('resolution_notes') or frappe.form_dict.get('resolution_notes', "")
    
    if not ticket_id:
        frappe.throw(_("Ticket ID is required"))
    
    if not frappe.db.exists("HD Ticket", ticket_id):
        frappe.throw(_("Ticket not found"))
    
    ticket = frappe.get_doc("HD Ticket", ticket_id)
    current_user = frappe.session.user
    
    # Check permissions: only ticket raiser or System Manager can mark as resolved
    if current_user != ticket.raised_by and not frappe.has_permission("HD Ticket", "delete"):
        frappe.throw(_("Only the ticket raiser or System Manager can mark tickets as resolved"))
    
    # Check if ticket is already closed or resolved
    if ticket.status in ["Closed", "Resolved"]:
        frappe.throw(_("Ticket is already {0}").format(ticket.status))
    
    # Mark as resolved
    ticket.status = "Resolved"
    ticket.resolution_date = now()
    
    # Add resolution comment
    if resolution_notes:
        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "ticket": ticket_id,
            "commented_by": current_user,
            "content": f"""
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin: 10px 0;">
                <strong>✅ Ticket Marked as Resolved</strong><br/>
                <strong>Resolution Notes:</strong><br/>
                {resolution_notes}
                <br/><br/>
                <em>Resolved by: {get_fullname(current_user)}</em>
            </div>
            """,
            "is_system": 1
        }).insert(ignore_permissions=True)
    
    ticket.save(ignore_permissions=True)
    
    # Send notification to assigned agents if any
    if hasattr(ticket, '_assign') and ticket._assign:
        try:
            import json
            assigned_users = json.loads(ticket._assign) if isinstance(ticket._assign, str) else ticket._assign
            
            for user in assigned_users:
                if user != current_user:
                    frappe.sendmail(
                        recipients=[user],
                        subject=f"Ticket #{ticket.name} Resolved",
                        message=f"""
                        <p>Hello,</p>
                        <p>Ticket <strong>#{ticket.name}</strong> has been marked as resolved by the customer.</p>
                        <p><strong>Subject:</strong> {ticket.subject}</p>
                        <p><strong>Resolution Notes:</strong></p>
                        <p>{resolution_notes}</p>
                        <p>Thank you for your assistance with this ticket.</p>
                        <p>Best regards,<br/>Support System</p>
                        """
                    )
        except Exception as e:
            frappe.log_error(f"Failed to send resolution notification: {str(e)}")
    
    return {
        "message": "Ticket marked as resolved successfully",
        "ticket_id": ticket_id,
        "status": ticket.status
    }


@frappe.whitelist()
def request_closure(**kwargs):
    """
    Request ticket closure by agents - sends notification to ticket raiser
    """
    ticket_id = kwargs.get('ticket_id') or frappe.form_dict.get('ticket_id')
    resolution_notes = kwargs.get('resolution_notes') or frappe.form_dict.get('resolution_notes')
    
    if not ticket_id:
        frappe.throw(_("Ticket ID is required"))
    
    if not resolution_notes:
        frappe.throw(_("Resolution notes are required"))
    
    if not frappe.db.exists("HD Ticket", ticket_id):
        frappe.throw(_("Ticket not found"))
    
    ticket = frappe.get_doc("HD Ticket", ticket_id)
    current_user = frappe.session.user
    
    # Check if user has permission to request closure (agents only)
    if not frappe.has_permission("HD Ticket", "write", doc=ticket):
        frappe.throw(_("You don't have permission to request closure for this ticket"))
    
    # Check if current user is the ticket raiser (they should use mark as resolved instead)
    if current_user == ticket.raised_by:
        frappe.throw(_("As the ticket raiser, please use 'Mark as Resolved' instead"))
    
    # Check if ticket is already closed or resolved
    if ticket.status in ["Closed", "Resolved"]:
        frappe.throw(_("Ticket is already {0}").format(ticket.status))
    
    # Create a comment indicating closure request
    comment = frappe.get_doc({
        "doctype": "HD Ticket Comment",
        "ticket": ticket_id,
        "commented_by": current_user,
        "content": f"""
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <strong>🔔 Closure Requested by Agent</strong><br/>
            <strong>Agent:</strong> {get_fullname(current_user)}<br/>
            <strong>Resolution Notes:</strong><br/>
            {resolution_notes}
            <br/><br/>
            <em>This ticket has been marked for closure by the resolving agent. 
            The ticket can be resolved by the person who raised it.</em>
        </div>
        """,
        "is_system": 1
    }).insert(ignore_permissions=True)
    
    # Set custom flag to track closure request
    ticket.add_comment("Info", f"Closure requested by {get_fullname(current_user)}: {resolution_notes}")
    ticket.save(ignore_permissions=True)
    
    # Send notification to ticket raiser
    if ticket.raised_by and ticket.raised_by != current_user:
        try:
            frappe.sendmail(
                recipients=[ticket.raised_by],
                subject=f"Closure Requested for Ticket #{ticket.name}",
                message=f"""
                <p>Hello,</p>
                <p>The agent working on your ticket <strong>#{ticket.name}</strong> has requested to close it.</p>
                <p><strong>Subject:</strong> {ticket.subject}</p>
                <p><strong>Agent:</strong> {get_fullname(current_user)}</p>
                <p><strong>Resolution Notes:</strong></p>
                <p>{resolution_notes}</p>
                <p>If you are satisfied with the resolution, you can mark the ticket as resolved. 
                Otherwise, please reply with additional questions or concerns.</p>
                <p><a href="{frappe.utils.get_url()}/app/hd-ticket/{ticket.name}" 
                   style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                   View Ticket
                </a></p>
                <p>Best regards,<br/>Support Team</p>
                """
            )
        except Exception as e:
            frappe.log_error(f"Failed to send closure notification: {str(e)}")
    
    return {
        "message": "Closure request submitted successfully. The ticket raiser has been notified.",
        "ticket_id": ticket_id,
        "status": ticket.status
    }


@frappe.whitelist()
def get_closure_permissions(**kwargs):
    """
    Get what closure actions are available for the current user on a ticket
    """
    # Get parameters from kwargs or form_dict
    ticket_id = kwargs.get('ticket_id') or frappe.form_dict.get('ticket_id')
    
    if not ticket_id:
        return {
            "can_mark_resolved": False, 
            "can_request_closure": False, 
            "error": "Ticket ID is required"
        }
    
    if not frappe.db.exists("HD Ticket", ticket_id):
        return {
            "can_mark_resolved": False, 
            "can_request_closure": False, 
            "error": "Ticket not found"
        }
    
    ticket = frappe.get_doc("HD Ticket", ticket_id)
    current_user = frappe.session.user
    
    # Check if ticket is already closed/resolved
    if ticket.status in ["Closed", "Resolved"]:
        return {"can_mark_resolved": False, "can_request_closure": False}
    
    # Ticket raiser can always mark as resolved
    can_mark_resolved = (current_user == ticket.raised_by or 
                        frappe.has_permission("HD Ticket", "delete"))
    
    # Agents can request closure (but not the ticket raiser)
    can_request_closure = (current_user != ticket.raised_by and 
                          frappe.has_permission("HD Ticket", "write", doc=ticket))
    
    return {
        "can_mark_resolved": can_mark_resolved,
        "can_request_closure": can_request_closure,
        "ticket_raiser": ticket.raised_by,
        "current_user": current_user
    } 