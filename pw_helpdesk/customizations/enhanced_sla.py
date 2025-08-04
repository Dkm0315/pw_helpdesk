import frappe
from frappe.model.document import Document
from helpdesk.helpdesk.doctype.hd_service_level_agreement.hd_service_level_agreement import HDServiceLevelAgreement
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket


class EnhancedSLA:
    """Enhanced SLA system that integrates with core Frappe logic"""
    
    @staticmethod
    def convert_categories_to_condition(sla_name, categories):
        """
        Convert a list of categories to a Python condition expression
        
        Args:
            sla_name: Name of the SLA
            categories: List of category names
            
        Returns:
            str: Python condition expression
        """
        if not categories:
            return None
            
        if len(categories) == 1:
            return f"doc.custom_category == '{categories[0]}'"
        else:
            category_list = "', '".join(categories)
            return f"doc.custom_category in ['{category_list}']"
    
    @staticmethod
    def migrate_multiselect_to_conditions():
        """
        Migrate existing HD Category MultiSelect entries to condition field
        """
        try:
            # Get all SLA records that use multiselect categories
            sla_category_map = {}
            
            # Collect categories for each SLA
            multiselect_entries = frappe.db.sql("""
                SELECT parent, category 
                FROM `tabHD Category MultiSelect`
                ORDER BY parent, category
            """, as_dict=True)
            
            for entry in multiselect_entries:
                if entry.parent not in sla_category_map:
                    sla_category_map[entry.parent] = []
                sla_category_map[entry.parent].append(entry.category)
            
            # Update each SLA with the equivalent condition
            for sla_name, categories in sla_category_map.items():
                condition = EnhancedSLA.convert_categories_to_condition(sla_name, categories)
                
                if condition:
                    frappe.db.set_value("HD Service Level Agreement", sla_name, "condition", condition)
                    frappe.msgprint(f"Migrated {sla_name} to use condition: {condition}")
            
            frappe.db.commit()
            frappe.msgprint("Successfully migrated all SLA categories to conditions")
            
        except Exception as e:
            frappe.log_error(f"Error migrating categories to conditions: {str(e)}")
            frappe.throw(f"Migration failed: {str(e)}")


# ENHANCED SLA APPLICATION - Override core method
original_apply = HDServiceLevelAgreement.apply

def enhanced_sla_apply(self, doc: Document):
    """
    Enhanced SLA application that includes team and agent assignment
    """
    try:
        # Call original SLA application logic first
        original_apply(self, doc)
        
        # Now handle our custom team assignment
        if hasattr(self, 'custom_auto_assign_team') and self.custom_auto_assign_team:
            doc.agent_group = self.custom_auto_assign_team
            
        # Handle agent assignment if we have an assignment rule
        if hasattr(self, 'custom_assignment_rule') and self.custom_assignment_rule:
            EnhancedSLA._assign_agent_via_rule(doc, self.custom_assignment_rule)
        elif doc.agent_group:
            # Fallback to team-based assignment
            EnhancedSLA._assign_agent_via_team(doc, doc.agent_group)
            
    except Exception as e:
        frappe.log_error(f"Error in enhanced SLA application: {str(e)}")
        # Don't break the flow - let core SLA continue
        
        
@staticmethod
def _assign_agent_via_rule(doc, assignment_rule_name):
    """Assign agent using assignment rule"""
    try:
        assignment_rule = frappe.get_doc("Assignment Rule", assignment_rule_name)
        
        if hasattr(assignment_rule, 'custom_user_assignment') and assignment_rule.custom_user_assignment:
            # Use Dynamic User Assignment
            user_assignment = frappe.get_doc("Dynamic User Assignment", assignment_rule.custom_user_assignment)
            if user_assignment.users:
                user_list = [user.user for user in user_assignment.users]
                
                if user_list:
                    # Simple round-robin assignment
                    ticket_number = int(doc.name.split('-')[-1]) if '-' in doc.name and doc.name.split('-')[-1].isdigit() else 1
                    selected_user = user_list[ticket_number % len(user_list)]
                    
                    # Use core assignment mechanism
                    from frappe.desk.form.assign_to import add
                    add({
                        "assign_to": [selected_user],
                        "doctype": doc.doctype,
                        "name": doc.name,
                        "description": f"Auto-assigned via SLA rule {assignment_rule_name}"
                    }, ignore_permissions=True)
                    
    except Exception as e:
        frappe.log_error(f"Error in rule-based assignment: {str(e)}")


@staticmethod  
def _assign_agent_via_team(doc, team_name):
    """Assign agent using team users"""
    try:
        team = frappe.get_doc("HD Team", team_name)
        
        # First try team's assignment rule
        if team.assignment_rule:
            EnhancedSLA._assign_agent_via_rule(doc, team.assignment_rule)
            return
            
        # Fallback to direct team users
        if team.users:
            ticket_number = int(doc.name.split('-')[-1]) if '-' in doc.name and doc.name.split('-')[-1].isdigit() else 1
            selected_user = team.users[ticket_number % len(team.users)].user
            
            from frappe.desk.form.assign_to import add
            add({
                "assign_to": [selected_user],
                "doctype": doc.doctype,
                "name": doc.name,
                "description": f"Auto-assigned from team {team_name}"
            }, ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(f"Error in team-based assignment: {str(e)}")


# Apply the enhanced SLA method
HDServiceLevelAgreement.apply = enhanced_sla_apply
HDServiceLevelAgreement._assign_agent_via_rule = _assign_agent_via_rule
HDServiceLevelAgreement._assign_agent_via_team = _assign_agent_via_team


# ENHANCED TICKET VALIDATION - Override set_sla to ensure our enhanced logic runs
original_apply_sla = HDTicket.apply_sla

def enhanced_apply_sla(self):
    """Enhanced apply_sla that triggers our enhanced SLA application"""
    try:
        if sla_doc := frappe.get_doc("HD Service Level Agreement", self.sla):
            sla_doc.apply(self)
    except Exception as e:
        frappe.log_error(f"Error applying enhanced SLA: {str(e)}")
        # Fallback to original logic
        original_apply_sla(self)

# Apply the enhanced apply_sla method
HDTicket.apply_sla = enhanced_apply_sla


# MIGRATION UTILITY
def run_migration():
    """Run the migration from multiselect to conditions"""
    EnhancedSLA.migrate_multiselect_to_conditions() 