import frappe
from pw_helpdesk.customizations.real_time_automation import RealTimeAutomation


def test_complete_real_time_workflow():
    """Test the complete real-time workflow"""
    
    print("🚀 Testing Complete Real-Time Workflow")
    print("=" * 50)
    
    # Step 1: Test Dynamic User Assignment sync to HD Team
    print('\n🔄 Step 1: Testing HD Team Dynamic User Sync')
    team = frappe.get_doc('HD Team', 'AI Support Team')
    print(f'   Team: {team.team_name}')
    print(f'   Dynamic Assignment: {team.custom_user_assignment}')
    print(f'   Current Users: {[u.user for u in team.users]}')
    
    # Get the actual dynamic assignment users
    if team.custom_user_assignment:
        dynamic_assignment = frappe.get_doc("Dynamic User Assignment", team.custom_user_assignment)
        expected_users = [user.user_id for user in dynamic_assignment.assigned_users]
        print(f'   Expected Users from Dynamic Assignment: {expected_users}')
        
        # Manually trigger team sync
        RealTimeAutomation.sync_team_users_from_dynamic_assignment(team, None)
        team.save(ignore_permissions=True)
        
        # Reload and check
        team.reload()
        print(f'   ✅ After Sync Users: {[u.user for u in team.users]}')
    
    # Step 2: Test SLA and team assignment
    print(f'\n🎫 Step 2: Testing SLA and Team Assignment')
    
    # Create a new ticket to test the complete flow
    ticket = frappe.new_doc("HD Ticket")
    ticket.subject = "Real-Time Workflow Test"
    ticket.description = "Testing complete real-time automation"
    ticket.raised_by = "admin@example.com"
    ticket.priority = "Medium"
    ticket.custom_category = "AI_AM_1"
    
    print(f'   Creating ticket with category: {ticket.custom_category}')
    
    # Insert the ticket and let our hooks handle the rest
    ticket.insert(ignore_permissions=True)
    
    print(f'   ✅ Ticket created: {ticket.name}')
    print(f'   SLA Applied: {ticket.sla}')
    
    # Check if team was assigned via SLA
    if ticket.sla:
        sla = frappe.get_doc('HD Service Level Agreement', ticket.sla)
        print(f'   SLA Team Setting: {sla.custom_auto_assign_team}')
        
        # Manually apply team assignment if not done automatically
        if sla.custom_auto_assign_team and not ticket.agent_group:
            ticket.agent_group = sla.custom_auto_assign_team
            ticket.save(ignore_permissions=True)
            print(f'   ✅ Agent Group set manually: {ticket.agent_group}')
        elif ticket.agent_group:
            print(f'   ✅ Agent Group already set: {ticket.agent_group}')
    
    # Step 3: Test Assignment Rule
    print(f'\n⚡ Step 3: Testing Assignment Rule')
    if ticket.sla:
        sla = frappe.get_doc('HD Service Level Agreement', ticket.sla)
        if sla.custom_assignment_rule:
            print(f'   Assignment Rule: {sla.custom_assignment_rule}')
            
            try:
                assignment_rule = frappe.get_doc('Assignment Rule', sla.custom_assignment_rule)
                print(f'   Rule Type: {assignment_rule.rule}')
                print(f'   Condition: {assignment_rule.assign_condition}')
                
                # Apply assignment rule
                assignment_rule.apply_assign(ticket)
                print(f'   ✅ Assignment rule applied')
                
            except Exception as e:
                print(f'   ⚠️  Assignment rule error: {str(e)}')
    
    # Step 4: Check final state
    print(f'\n📋 Step 4: Final Results')
    ticket.reload()
    print(f'   Ticket: {ticket.name}')
    print(f'   Category: {ticket.custom_category}')
    print(f'   SLA: {ticket.sla}')
    print(f'   Agent Group: {getattr(ticket, "agent_group", "None")}')
    
    # Check ToDo assignments
    assignments = frappe.db.sql("""
        SELECT allocated_to, status, description 
        FROM `tabToDo`
        WHERE reference_type = 'HD Ticket' AND reference_name = %s
        ORDER BY creation DESC
    """, ticket.name, as_dict=True)
    
    if assignments:
        print(f'   📝 Assignments:')
        for assignment in assignments:
            print(f'      - {assignment.allocated_to} ({assignment.status})')
    else:
        print(f'   ⚠️  No assignments found')
    
    print(f'\n🎉 Real-time workflow test completed!')
    return ticket.name


def test_real_time_condition_generation():
    """Test real-time condition generation"""
    
    print("\n🔧 Testing Real-Time Condition Generation")
    print("=" * 50)
    
    # Test SLA condition generation
    sla = frappe.get_doc("HD Service Level Agreement", "AI Support SLA")
    print(f'\nSLA: {sla.service_level}')
    print(f'Current Categories: {[cat.category for cat in sla.custom_applicable_categories]}')
    print(f'Current Condition: {sla.condition}')
    
    # Test real-time validation
    RealTimeAutomation.auto_update_sla_condition(sla, None)
    print(f'Auto-generated Condition: {sla.condition}')
    
    # Test Assignment Rule condition generation
    assignment_rules = frappe.get_all("Assignment Rule", 
                                    filters={"document_type": "HD Ticket"},
                                    fields=["name"])
    
    for rule_info in assignment_rules:
        rule = frappe.get_doc("Assignment Rule", rule_info.name)
        print(f'\nAssignment Rule: {rule.name}')
        if hasattr(rule, 'custom_applicable_categories') and rule.custom_applicable_categories:
            print(f'Current Categories: {[cat.category for cat in rule.custom_applicable_categories]}')
            print(f'Current Condition: {rule.assign_condition}')
            
            # Test real-time validation
            RealTimeAutomation.auto_update_assignment_rule_condition(rule, None)
            print(f'Auto-generated Condition: {rule.assign_condition}')


if __name__ == "__main__":
    # Test complete workflow
    ticket_name = test_complete_real_time_workflow()
    
    # Test condition generation
    test_real_time_condition_generation()
    
    print(f"\n✅ All tests completed! Test ticket: {ticket_name}") 