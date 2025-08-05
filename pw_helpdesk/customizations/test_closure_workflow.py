import frappe
from frappe import _
from pw_helpdesk.customizations.ticket_closure_workflow import (
    mark_as_resolved, 
    request_closure, 
    get_closure_permissions
)


def test_complete_closure_workflow():
    """
    Test the complete ticket closure workflow with different user scenarios
    """
    print("🎯 Testing Complete Closure Workflow")
    print("=" * 60)
    
    # Create test users if they don't exist
    setup_test_users()
    
    # Create a test ticket
    ticket = create_test_ticket()
    print(f"\n📝 Created test ticket: {ticket.name}")
    print(f"   Raised by: {ticket.raised_by}")
    print(f"   Status: {ticket.status}")
    
    # Test 1: Check permissions for ticket raiser
    print(f"\n🔍 Test 1: Permissions for ticket raiser")
    test_permissions_as_user(ticket.name, "customer@test.com")
    
    # Test 2: Check permissions for agent
    print(f"\n🔍 Test 2: Permissions for agent")
    test_permissions_as_user(ticket.name, "agent1@test.com")
    
    # Test 3: Test request closure by agent
    print(f"\n🔄 Test 3: Request closure by agent")
    test_request_closure_as_agent(ticket.name)
    
    # Test 4: Test mark as resolved by customer
    print(f"\n✅ Test 4: Mark as resolved by customer")
    test_mark_as_resolved_by_customer(ticket.name)
    
    print(f"\n🎉 Closure workflow testing completed!")
    return ticket.name


def setup_test_users():
    """Create test users if they don't exist"""
    users = [
        {
            "email": "customer@test.com",
            "first_name": "Test",
            "last_name": "Customer",
            "roles": ["Customer"]
        },
        {
            "email": "agent1@test.com", 
            "first_name": "Agent",
            "last_name": "One",
            "roles": ["Agent"]
        }
    ]
    
    for user_data in users:
        if not frappe.db.exists("User", user_data["email"]):
            try:
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "send_welcome_email": 0,
                    "user_type": "System User"
                })
                user.insert(ignore_permissions=True)
                
                # Add roles
                for role in user_data["roles"]:
                    user.add_roles(role)
                
                print(f"   Created test user: {user_data['email']}")
            except Exception as e:
                print(f"   User {user_data['email']} already exists or error: {str(e)}")


def create_test_ticket():
    """Create a test ticket for closure workflow testing"""
    ticket = frappe.new_doc("HD Ticket")
    ticket.subject = "Closure Workflow Test Ticket"
    ticket.description = "This is a test ticket for testing the closure workflow"
    ticket.raised_by = "customer@test.com"
    ticket.priority = "Medium"
    ticket.custom_category = "AI_AM_1"
    ticket.status = "Open"
    
    ticket.insert(ignore_permissions=True)
    
    # Assign to an agent
    try:
        from frappe.desk.form.assign_to import add as assign_to_add
        assign_to_add({
            "assign_to": ["agent1@test.com"],
            "doctype": "HD Ticket",
            "name": ticket.name,
            "description": "Assigned for closure workflow testing"
        })
        print(f"   Assigned ticket to agent1@test.com")
    except Exception as e:
        print(f"   Assignment error: {str(e)}")
    
    return ticket


def test_permissions_as_user(ticket_id, user_email):
    """Test closure permissions for a specific user"""
    # Temporarily switch user context
    original_user = frappe.session.user
    frappe.set_user(user_email)
    
    try:
        permissions = get_closure_permissions(ticket_id)
        print(f"   User: {user_email}")
        print(f"   Can Mark Resolved: {permissions['can_mark_resolved']}")
        print(f"   Can Request Closure: {permissions['can_request_closure']}")
        print(f"   Current User: {permissions['current_user']}")
        print(f"   Ticket Raiser: {permissions['ticket_raiser']}")
        
        return permissions
        
    except Exception as e:
        print(f"   Error checking permissions: {str(e)}")
        return None
    finally:
        frappe.set_user(original_user)


def test_request_closure_as_agent(ticket_id):
    """Test requesting closure as an agent"""
    original_user = frappe.session.user
    frappe.set_user("agent1@test.com")
    
    try:
        result = request_closure(ticket_id, "Issue has been resolved. Customer can verify and close.")
        print(f"   ✅ Request closure successful")
        print(f"   Message: {result['message']}")
        print(f"   Status: {result['status']}")
        
        # Check if comment was created
        comments = frappe.get_all(
            "HD Ticket Comment",
            filters={"ticket": ticket_id},
            fields=["content", "commented_by"],
            order_by="creation desc",
            limit=1
        )
        
        if comments:
            print(f"   Comment created by: {comments[0]['commented_by']}")
            print(f"   Comment contains closure request: {'Closure Requested' in comments[0]['content']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Request closure failed: {str(e)}")
        return False
    finally:
        frappe.set_user(original_user)


def test_mark_as_resolved_by_customer(ticket_id):
    """Test marking ticket as resolved by the customer"""
    original_user = frappe.session.user
    frappe.set_user("customer@test.com")
    
    try:
        result = mark_as_resolved(ticket_id, "Thank you for the resolution. The issue is now fixed.")
        print(f"   ✅ Mark as resolved successful")
        print(f"   Message: {result['message']}")
        print(f"   Status: {result['status']}")
        
        # Verify ticket status changed
        ticket = frappe.get_doc("HD Ticket", ticket_id)
        print(f"   Final ticket status: {ticket.status}")
        print(f"   Resolution date set: {ticket.resolution_date is not None}")
        
        # Check if resolution comment was created
        comments = frappe.get_all(
            "HD Ticket Comment",
            filters={"ticket": ticket_id},
            fields=["content", "commented_by"],
            order_by="creation desc",
            limit=1
        )
        
        if comments:
            print(f"   Resolution comment created by: {comments[0]['commented_by']}")
            print(f"   Comment contains resolution: {'Marked as Resolved' in comments[0]['content']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Mark as resolved failed: {str(e)}")
        return False
    finally:
        frappe.set_user(original_user)


def test_error_scenarios():
    """Test error scenarios for the closure workflow"""
    print(f"\n🚨 Testing Error Scenarios")
    print("=" * 40)
    
    # Create another test ticket
    ticket = create_test_ticket()
    original_user = frappe.session.user
    
    try:
        # Test 1: Agent trying to mark as resolved (should fail)
        print(f"\n❌ Test: Agent trying to mark as resolved")
        frappe.set_user("agent1@test.com")
        try:
            mark_as_resolved(ticket.name, "Agent trying to resolve")
            print(f"   FAIL: Agent was allowed to mark as resolved")
        except Exception as e:
            print(f"   ✅ PASS: Agent correctly blocked: {str(e)}")
        
        # Test 2: Customer trying to request closure (should fail)
        print(f"\n❌ Test: Customer trying to request closure")
        frappe.set_user("customer@test.com")
        try:
            request_closure(ticket.name, "Customer trying to request closure")
            print(f"   FAIL: Customer was allowed to request closure")
        except Exception as e:
            print(f"   ✅ PASS: Customer correctly blocked: {str(e)}")
        
        # Test 3: Operations on already resolved ticket (should fail)
        print(f"\n❌ Test: Operations on resolved ticket")
        ticket.status = "Resolved"
        ticket.save(ignore_permissions=True)
        
        frappe.set_user("agent1@test.com")
        try:
            request_closure(ticket.name, "Trying on resolved ticket")
            print(f"   FAIL: Request closure allowed on resolved ticket")
        except Exception as e:
            print(f"   ✅ PASS: Request closure blocked on resolved ticket: {str(e)}")
        
    finally:
        frappe.set_user(original_user)


def test_form_script_creation():
    """Test that our HD Form Script was created correctly"""
    print(f"\n📋 Testing HD Form Script Creation")
    print("=" * 40)
    
    # Check if our form script exists
    scripts = frappe.get_all(
        "HD Form Script",
        filters={"dt": "HD Ticket", "enabled": 1},
        fields=["name", "script"],
        order_by="creation desc",
        limit=5
    )
    
    print(f"   Found {len(scripts)} HD Form Scripts for HD Ticket")
    
    # Check our specific script
    our_script = None
    for script in scripts:
        if "Mark as Resolved" in script["script"] and "Request Closure" in script["script"]:
            our_script = script
            break
    
    if our_script:
        print(f"   ✅ Closure workflow form script found: {our_script['name']}")
        print(f"   Script contains conditional logic: {'currentUser === ticketRaiser' in our_script['script']}")
        print(f"   Script has proper dialogs: {'showResolutionDialog' in our_script['script']}")
    else:
        print(f"   ❌ Closure workflow form script not found")
    
    return our_script is not None


if __name__ == "__main__":
    try:
        # Test form script creation
        test_form_script_creation()
        
        # Test closure workflow
        test_complete_closure_workflow()
        
        # Test error scenarios
        test_error_scenarios()
        
        print(f"\n🏆 All closure workflow tests completed!")
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc() 