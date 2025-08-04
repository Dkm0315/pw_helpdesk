import frappe
from frappe import _
from frappe.model.document import Document


class RealTimeAutomation:
    """Real-time automation for category conditions and dynamic user sync"""

    @staticmethod
    def auto_update_sla_condition(doc, method=None):
        """
        Automatically update SLA condition when categories are modified
        Called on validate of HD Service Level Agreement
        """
        if doc.doctype != "HD Service Level Agreement":
            return
            
        try:
            # Only auto-generate if we have categories selected
            if hasattr(doc, 'custom_applicable_categories') and doc.custom_applicable_categories:
                categories = [row.category for row in doc.custom_applicable_categories if row.category]
                
                if categories:
                    # Generate condition automatically
                    if len(categories) == 1:
                        new_condition = f"doc.custom_category == '{categories[0]}'"
                    else:
                        category_list = "', '".join(categories)
                        new_condition = f"doc.custom_category in ['{category_list}']"
                    
                    # Update condition if it's different
                    if doc.condition != new_condition:
                        doc.condition = new_condition
                        frappe.msgprint(f"✅ Condition auto-updated: {new_condition}", indicator="green")
                        
        except Exception as e:
            frappe.log_error(f"Error in auto_update_sla_condition: {str(e)}")

    @staticmethod
    def auto_update_assignment_rule_condition(doc, method=None):
        """
        Automatically update Assignment Rule condition when categories are modified
        Called on validate of Assignment Rule
        """
        if doc.doctype != "Assignment Rule" or doc.document_type != "HD Ticket":
            return
            
        try:
            # Only auto-generate if we have categories selected
            if hasattr(doc, 'custom_applicable_categories') and doc.custom_applicable_categories:
                categories = [row.category for row in doc.custom_applicable_categories if row.category]
                
                if categories:
                    # Generate assignment condition automatically
                    if len(categories) == 1:
                        new_condition = f"custom_category == '{categories[0]}'"
                    else:
                        category_list = "', '".join(categories)
                        new_condition = f"custom_category in ['{category_list}']"
                    
                    # Update condition if it's different
                    if doc.assign_condition != new_condition:
                        doc.assign_condition = new_condition
                        frappe.msgprint(f"✅ Assignment condition auto-updated: {new_condition}", indicator="green")
                        
        except Exception as e:
            frappe.log_error(f"Error in auto_update_assignment_rule_condition: {str(e)}")

    @staticmethod
    def sync_team_users_from_dynamic_assignment(doc, method=None):
        """
        Automatically sync HD Team users from Dynamic User Assignment
        Called on validate and after_save of HD Team
        """
        if doc.doctype != "HD Team":
            return
            
        try:
            # Check if team has custom_user_assignment linked
            if hasattr(doc, 'custom_user_assignment') and doc.custom_user_assignment:
                # Get users from Dynamic User Assignment
                dynamic_assignment = frappe.get_doc("Dynamic User Assignment", doc.custom_user_assignment)
                
                if dynamic_assignment.assigned_users:
                    # Get current users in team
                    current_users = [user.user for user in doc.users] if doc.users else []
                    
                    # Get users from dynamic assignment
                    dynamic_users = [user.user_id for user in dynamic_assignment.assigned_users]
                    
                    # Only update if there's a difference
                    if set(current_users) != set(dynamic_users):
                        # Clear existing users
                        doc.users = []
                        
                        # Add users from dynamic assignment
                        for user_row in dynamic_assignment.assigned_users:
                            if user_row.user_id:
                                doc.append("users", {"user": user_row.user_id})
                        
                        frappe.msgprint(f"✅ Team users synced from Dynamic User Assignment: {dynamic_users}", indicator="green")
                        
                        # Also ensure these users exist as HD Agents
                        RealTimeAutomation.ensure_hd_agents_exist(dynamic_users)
                        
        except Exception as e:
            frappe.log_error(f"Error in sync_team_users_from_dynamic_assignment: {str(e)}")

    @staticmethod
    def ensure_hd_agents_exist(users):
        """Ensure HD Agent records exist for all users"""
        for user in users:
            if user and not frappe.db.exists("HD Agent", user):
                try:
                    agent = frappe.new_doc("HD Agent")
                    agent.user = user
                    agent.is_active = 1
                    agent.save(ignore_permissions=True)
                    print(f"Created HD Agent for {user}")
                except Exception as e:
                    frappe.log_error(f"Error creating HD Agent for {user}: {str(e)}")

    @staticmethod
    def auto_set_team_assignment_rule(doc, method=None):
        """
        Automatically set assignment rule in SLA from the team's assignment rule
        Called on validate of HD Service Level Agreement
        """
        if doc.doctype != "HD Service Level Agreement":
            return
            
        try:
            # If team is selected but assignment rule is not, auto-set it
            if hasattr(doc, 'custom_auto_assign_team') and doc.custom_auto_assign_team:
                if not hasattr(doc, 'custom_assignment_rule') or not doc.custom_assignment_rule:
                    
                    # Get team's assignment rule
                    team = frappe.get_doc("HD Team", doc.custom_auto_assign_team)
                    if team.assignment_rule:
                        doc.custom_assignment_rule = team.assignment_rule
                        frappe.msgprint(f"✅ Assignment rule auto-set from team: {team.assignment_rule}", indicator="blue")
                        
        except Exception as e:
            frappe.log_error(f"Error in auto_set_team_assignment_rule: {str(e)}")

    @staticmethod
    def enhanced_agent_assignment(doc, method=None):
        """
        Enhanced agent assignment that uses team's dynamic user assignment
        Called on after_insert and after_save of HD Ticket
        """
        if doc.doctype != "HD Ticket":
            return
            
        try:
            # Skip if no agent group is set
            if not hasattr(doc, 'agent_group') or not doc.agent_group:
                return
                
            # Get the team
            team = frappe.get_doc("HD Team", doc.agent_group)
            
            # Check if team has dynamic user assignment
            if hasattr(team, 'custom_user_assignment') and team.custom_user_assignment:
                # Sync users from dynamic assignment first
                RealTimeAutomation.sync_team_users_from_dynamic_assignment(team, None)
                team.save(ignore_permissions=True)
            
            # Use team's assignment rule if available
            assignment_rule = None
            if team.assignment_rule:
                assignment_rule = team.assignment_rule
            elif hasattr(doc, 'sla') and doc.sla:
                # Fallback to SLA's assignment rule
                sla = frappe.get_doc("HD Service Level Agreement", doc.sla)
                if hasattr(sla, 'custom_assignment_rule') and sla.custom_assignment_rule:
                    assignment_rule = sla.custom_assignment_rule
            
            # Assign using the assignment rule
            if assignment_rule:
                try:
                    rule = frappe.get_doc("Assignment Rule", assignment_rule)
                    rule.apply_assign(doc)
                    print(f"Applied assignment rule {assignment_rule} to ticket {doc.name}")
                except Exception as e:
                    frappe.log_error(f"Error applying assignment rule {assignment_rule}: {str(e)}")
                    
        except Exception as e:
            frappe.log_error(f"Error in enhanced_agent_assignment: {str(e)}")


# Hook functions for registering in hooks.py

def sla_real_time_validation(doc, method):
    """Real-time SLA validation and auto-updates"""
    RealTimeAutomation.auto_update_sla_condition(doc, method)
    RealTimeAutomation.auto_set_team_assignment_rule(doc, method)

def assignment_rule_real_time_validation(doc, method):
    """Real-time Assignment Rule validation and auto-updates"""
    RealTimeAutomation.auto_update_assignment_rule_condition(doc, method)

def team_real_time_sync(doc, method):
    """Real-time HD Team user sync from Dynamic User Assignment"""
    RealTimeAutomation.sync_team_users_from_dynamic_assignment(doc, method)

def ticket_enhanced_assignment(doc, method):
    """Enhanced ticket assignment with dynamic user sync"""
    RealTimeAutomation.enhanced_agent_assignment(doc, method) 