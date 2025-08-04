import frappe
from frappe.model.document import Document
from frappe import _
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket

# MONKEY PATCH: Fix core permission issue in on_communication_update
def patched_on_communication_update(self, c):
    """
    Fixed version of on_communication_update that uses ignore_permissions=True
    to prevent permission errors during ticket updates from communication creation.
    """
    # If communication is incoming, then it is a reply from customer, and ticket must
    # be reopened.
    if c.sent_or_received == "Received":
        self.status = "Open"
    # If communication is outgoing, it must be a reply from agent
    if c.sent_or_received == "Sent":
        # Set first response date if not set already
        self.first_responded_on = (
            self.first_responded_on or frappe.utils.now_datetime()
        )

        if frappe.db.get_single_value("HD Settings", "auto_update_status"):
            self.status = "Replied"

    # Fetch description from communication if not set already. This might not be needed
    # anymore as a communication is created when a ticket is created.
    self.description = self.description or c.content
    
    # CRITICAL FIX: Set flag to prevent assignment rule from running during this save
    # This prevents permission errors during the communication update process
    self.flags.ignore_assignment_rule = True
    
    # Save the ticket, allowing for hooks to run - FIXED: Added ignore_permissions=True
    self.save(ignore_permissions=True)
    
    # Clear the flag after save
    self.flags.ignore_assignment_rule = False

# Apply the monkey patch
HDTicket.on_communication_update = patched_on_communication_update

# MONKEY PATCH: Fix Assignment Rule permission issues
from frappe.automation.doctype.assignment_rule.assignment_rule import AssignmentRule

original_apply = AssignmentRule.apply_assign

def patched_apply_assign(self, doc):
    """Fixed version of apply_assign that handles permissions correctly"""
    try:
        # Check if assignment rule should be ignored (e.g., during communication updates)
        if hasattr(doc, 'flags') and getattr(doc.flags, 'ignore_assignment_rule', False):
            return False
            
        return original_apply(self, doc)
    except frappe.PermissionError as e:
        # Log the permission error but don't break the flow
        frappe.log_error(f"Assignment Rule permission error for {doc.doctype} {doc.name}: {str(e)}")
        return False
    except Exception as e:
        # Handle any other assignment errors gracefully
        frappe.log_error(f"Assignment Rule error for {doc.doctype} {doc.name}: {str(e)}")
        return False

# Apply the assignment rule monkey patch
AssignmentRule.apply_assign = patched_apply_assign


def validate_ticket_closure(doc, method):
    """Validate that all required fields are filled before closing a ticket"""
    if doc.status == "Closed":
        if not doc.resolution_details:
            frappe.throw("Resolution Details are required before closing a ticket")
        if not doc.resolution_date:
            doc.resolution_date = frappe.utils.now_datetime()


def auto_assign_agents_after_save(doc, method):
    """
    Auto-assign agents after ticket save - this is now simplified 
    since most logic is handled in the enhanced SLA system
    """
    try:
        # Enhanced SLA system now handles most assignment logic
        # This function now mainly serves as a fallback for edge cases
        
        if not doc.agent_group:
            return
            
        # Check if ticket is already assigned
        existing_assignments = frappe.db.sql("""
            SELECT allocated_to FROM `tabToDo` 
            WHERE reference_type = 'HD Ticket' AND reference_name = %s 
            AND status = 'Open'
        """, doc.name, as_dict=True)
        
        if existing_assignments:
            # Already assigned, nothing to do
            return
            
        # Fallback assignment if enhanced SLA didn't handle it
        _fallback_team_assignment(doc)
        
    except Exception as e:
        frappe.log_error(f"Error in simplified auto-assignment: {str(e)}")


def _fallback_team_assignment(doc):
    """Fallback method for team-based assignment"""
    try:
        team = frappe.get_doc("HD Team", doc.agent_group)
        
        if team.users:
            # Simple round-robin from team users
            ticket_number = int(doc.name.split('-')[-1]) if '-' in doc.name and doc.name.split('-')[-1].isdigit() else 1
            selected_user = team.users[ticket_number % len(team.users)].user
            
            from frappe.desk.form.assign_to import add
            add({
                "assign_to": [selected_user],
                "doctype": "HD Ticket", 
                "name": doc.name,
                "description": f"Fallback assignment from team {team.name}"
            }, ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(f"Error in fallback team assignment: {str(e)}")


def sync_team_users_from_dynamic_assignment(team_name):
    """Sync users from Dynamic User Assignment to HD Team users field"""
    try:
        team_doc = frappe.get_doc("HD Team", team_name)
        
        # Check if team has dynamic user assignment configured
        if not hasattr(team_doc, 'custom_user_assignment') or not team_doc.custom_user_assignment:
            return
            
        # Get users from Dynamic User Assignment
        dynamic_assignment = frappe.get_doc("Dynamic User Assignment", team_doc.custom_user_assignment)
        
        # Clear existing users
        team_doc.users = []
        
        # Add users from Dynamic User Assignment
        for user_row in dynamic_assignment.users:
            if user_row.user:
                # Create HD Agent if doesn't exist
                if not frappe.db.exists("HD Agent", user_row.user):
                    create_hd_agent(user_row.user)
                
                # Add to team users
                team_doc.append("users", {
                    "user": user_row.user
                })
        
        # Save team with updated users
        team_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.msgprint(f"Team '{team_name}' users synced from Dynamic User Assignment")
        
    except Exception as e:
        frappe.log_error(f"Error syncing team users from Dynamic User Assignment: {str(e)}", "Team User Sync Error")


def create_hd_agent(user_email):
    """Create HD Agent record for user if it doesn't exist"""
    try:
        if frappe.db.exists("HD Agent", user_email):
            return
            
        user_doc = frappe.get_doc("User", user_email)
        
        agent_doc = frappe.new_doc("HD Agent")
        agent_doc.user = user_email
        agent_doc.agent_name = user_doc.full_name or user_email
        agent_doc.is_active = 1
        agent_doc.save(ignore_permissions=True)
        
        frappe.db.commit()
        frappe.msgprint(f"HD Agent created for user: {user_email}")
        
    except Exception as e:
        frappe.log_error(f"Error creating HD Agent for {user_email}: {str(e)}", "HD Agent Creation Error")


def on_team_save(doc, method):
    """Sync users when HD Team is saved"""
    try:
        if hasattr(doc, 'custom_user_assignment') and doc.custom_user_assignment:
            sync_team_users_from_dynamic_assignment(doc.name)
    except Exception as e:
        frappe.log_error(f"Error in team save event: {str(e)}", "Team Save Error")


def on_ticket_comment_insert(doc, method):
    """Handle ticket comment insertion events"""
    try:
        # Add any custom logic for comment handling here
        pass
    except Exception as e:
        frappe.log_error(f"Error in ticket comment event: {str(e)}", "Comment Event Error") 