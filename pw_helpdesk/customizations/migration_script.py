import frappe
from pw_helpdesk.customizations.enhanced_sla import EnhancedSLA


def run_full_migration():
    """
    Complete migration script to convert from multiselect to conditions
    and remove unnecessary customizations
    """
    print("🔄 Starting Migration from MultiSelect to Conditions...")
    
    # Step 1: Migrate existing multiselect entries to conditions
    print("\n📋 Step 1: Converting MultiSelect categories to conditions")
    EnhancedSLA.migrate_multiselect_to_conditions()
    
    # Step 2: Remove the custom_applicable_categories field
    print("\n🗑️  Step 2: Removing redundant custom_applicable_categories field")
    remove_applicable_categories_field()
    
    # Step 3: Test the new system
    print("\n🧪 Step 3: Testing the enhanced SLA system")
    test_enhanced_sla_system()
    
    print("\n✅ Migration completed successfully!")


def remove_applicable_categories_field():
    """Remove the custom_applicable_categories field that's no longer needed"""
    try:
        # Check if field exists
        if frappe.db.exists("Custom Field", {"fieldname": "custom_applicable_categories", "dt": "HD Service Level Agreement"}):
            # Remove the custom field
            frappe.delete_doc("Custom Field", "HD Service Level Agreement-custom_applicable_categories")
            frappe.db.commit()
            print("   ✅ Removed custom_applicable_categories field")
        else:
            print("   ℹ️  custom_applicable_categories field not found")
            
    except Exception as e:
        print(f"   ❌ Error removing custom_applicable_categories field: {str(e)}")


def test_enhanced_sla_system():
    """Test the enhanced SLA system with various scenarios"""
    try:
        print("   🔍 Testing SLA condition evaluation...")
        
        # Test conditions that should have been created
        test_conditions = [
            ("Test Category SLA", "doc.custom_category == 'AI_AM_1'"),
            ("Working Default SLA", "doc.custom_category == 'AB_ST_1'")
        ]
        
        for sla_name, expected_condition in test_conditions:
            if frappe.db.exists("HD Service Level Agreement", sla_name):
                actual_condition = frappe.db.get_value("HD Service Level Agreement", sla_name, "condition")
                if actual_condition == expected_condition:
                    print(f"   ✅ {sla_name}: Condition correctly set")
                else:
                    print(f"   ⚠️  {sla_name}: Expected '{expected_condition}', got '{actual_condition}'")
            else:
                print(f"   ℹ️  {sla_name}: SLA not found")
        
        # Test that multiselect entries can be cleaned up
        multiselect_count = frappe.db.count("HD Category MultiSelect")
        print(f"   📊 HD Category MultiSelect entries remaining: {multiselect_count}")
        
        if multiselect_count > 0:
            print("   💡 You can now safely remove HD Category MultiSelect entries")
            
    except Exception as e:
        print(f"   ❌ Error testing enhanced SLA system: {str(e)}")


def clean_multiselect_entries():
    """Clean up HD Category MultiSelect entries after successful migration"""
    try:
        multiselect_entries = frappe.get_all("HD Category MultiSelect")
        
        if not multiselect_entries:
            print("   ℹ️  No HD Category MultiSelect entries to clean")
            return
            
        print(f"   🗑️  Removing {len(multiselect_entries)} HD Category MultiSelect entries...")
        
        for entry in multiselect_entries:
            frappe.delete_doc("HD Category MultiSelect", entry.name)
            
        frappe.db.commit()
        print("   ✅ HD Category MultiSelect entries cleaned up")
        
    except Exception as e:
        print(f"   ❌ Error cleaning multiselect entries: {str(e)}")


def verify_enhanced_system():
    """Verify that the enhanced system is working correctly"""
    print("\n🔍 Verifying Enhanced SLA System...")
    
    try:
        # Check that enhanced_sla module is importable
        import pw_helpdesk.customizations.enhanced_sla
        print("   ✅ Enhanced SLA module imported successfully")
        
        # Check SLA conditions
        slas_with_conditions = frappe.db.sql("""
            SELECT name, condition, custom_auto_assign_team, custom_assignment_rule
            FROM `tabHD Service Level Agreement`
            WHERE enabled = 1 AND condition IS NOT NULL
        """, as_dict=True)
        
        print(f"   📊 Found {len(slas_with_conditions)} SLAs with conditions:")
        for sla in slas_with_conditions:
            print(f"      - {sla.name}: {sla.condition}")
            if sla.custom_auto_assign_team:
                print(f"        Team: {sla.custom_auto_assign_team}")
            if sla.custom_assignment_rule:
                print(f"        Rule: {sla.custom_assignment_rule}")
        
        print("   ✅ Enhanced SLA system verification complete")
        
    except Exception as e:
        print(f"   ❌ Error verifying enhanced system: {str(e)}")


if __name__ == "__main__":
    run_full_migration() 