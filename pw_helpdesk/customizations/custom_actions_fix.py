"""
Monkey patch to fix CustomActions.vue onClick error
This ensures all custom actions have proper onClick functions to prevent runtime errors
"""

import frappe
from frappe import _


def apply_custom_actions_fix():
    """
    Apply fixes to ensure custom actions work properly
    This can be called during app installation or migration
    """
    print("🔧 Applying Custom Actions fixes...")
    
    # Fix any existing HD Form Scripts that might have malformed actions
    fix_existing_form_scripts()
    
    print("✅ Custom Actions fixes applied successfully")


def fix_existing_form_scripts():
    """
    Fix any existing HD Form Scripts that might have actions without proper onClick functions
    """
    try:
        # Get all HD Form Scripts for HD Ticket
        scripts = frappe.get_all(
            "HD Form Script",
            filters={"dt": "HD Ticket", "enabled": 1},
            fields=["name", "script"]
        )
        
        fixed_count = 0
        for script_info in scripts:
            script_doc = frappe.get_doc("HD Form Script", script_info.name)
            
            # Check if script has potential onClick issues
            if "onClick" in script_doc.script and "function" not in script_doc.script:
                # This script might have issues, let's enhance it
                enhanced_script = enhance_form_script(script_doc.script)
                if enhanced_script != script_doc.script:
                    script_doc.script = enhanced_script
                    script_doc.save(ignore_permissions=True)
                    fixed_count += 1
                    print(f"   Fixed HD Form Script: {script_doc.name}")
        
        if fixed_count > 0:
            print(f"   Fixed {fixed_count} HD Form Scripts")
        else:
            print("   No HD Form Scripts needed fixing")
            
    except Exception as e:
        frappe.log_error(f"Error fixing form scripts: {str(e)}")
        print(f"   Error fixing scripts: {str(e)}")


def enhance_form_script(script_content):
    """
    Enhance form script to ensure all actions have proper onClick functions
    """
    # Add validation wrapper to ensure onClick functions exist
    wrapper = """
// Enhanced script with onClick validation
function validateAction(action) {
    if (action && typeof action.onClick !== 'function') {
        console.warn('Action missing onClick function:', action);
        action.onClick = function() {
            console.warn('No onClick handler defined for action:', action.label);
        };
    }
    return action;
}

"""
    
    # If the script doesn't already have the wrapper, add it
    if "validateAction" not in script_content:
        # Find the return statement and enhance it
        if "return {" in script_content and "actions:" in script_content:
            # Add validation to actions array
            enhanced = script_content.replace(
                "actions: actions",
                "actions: actions.map(validateAction)"
            )
            
            if enhanced != script_content:
                return wrapper + enhanced
    
    return script_content


@frappe.whitelist()
def validate_custom_actions(actions):
    """
    Validate and fix custom actions to ensure they have proper onClick functions
    This can be called from the frontend to ensure actions are valid
    """
    if not isinstance(actions, list):
        return []
    
    validated_actions = []
    for action in actions:
        if isinstance(action, dict):
            # Ensure the action has required properties
            if 'label' not in action:
                continue
                
            # Ensure onClick is callable or provide a default
            if 'onClick' not in action or not callable(action.get('onClick')):
                action['onClick'] = lambda: frappe.msgprint(_("Action handler not properly configured"))
            
            validated_actions.append(action)
    
    return validated_actions


def install_custom_actions_fix():
    """
    Install the custom actions fix during app installation
    """
    try:
        apply_custom_actions_fix()
        
        # Create a custom system setting to track that we've applied the fix
        if not frappe.db.exists("System Settings", "pw_helpdesk_custom_actions_fix"):
            frappe.get_doc({
                "doctype": "System Settings",
                "name": "pw_helpdesk_custom_actions_fix",
                "value": "applied"
            }).insert(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(f"Error installing custom actions fix: {str(e)}")


if __name__ == "__main__":
    apply_custom_actions_fix() 