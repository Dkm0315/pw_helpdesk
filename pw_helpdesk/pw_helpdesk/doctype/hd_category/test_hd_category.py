import frappe
import unittest
from frappe.tests.utils import FrappeTestCase


class TestHDCategory(FrappeTestCase):
    def setUp(self):
        """Set up test data"""
        # Create a test category
        self.test_category = frappe.get_doc({
            "doctype": "HD Category",
            "category_name": "Test Category",
            "category_code": "TEST_CAT",
            "description": "Test category for unit testing",
            "is_active": 1
        })
        self.test_category.insert()

    def tearDown(self):
        """Clean up test data"""
        if self.test_category:
            self.test_category.delete()

    def test_category_creation(self):
        """Test basic category creation"""
        self.assertTrue(self.test_category.name)
        self.assertEqual(self.test_category.category_name, "Test Category")
        self.assertEqual(self.test_category.category_code, "TEST_CAT")

    def test_category_code_uniqueness(self):
        """Test that category codes must be unique"""
        duplicate_category = frappe.get_doc({
            "doctype": "HD Category",
            "category_name": "Duplicate Category",
            "category_code": "TEST_CAT",  # Same code as test category
            "description": "Duplicate category"
        })
        
        with self.assertRaises(frappe.ValidationError):
            duplicate_category.insert()

    def test_assignee_email_validation(self):
        """Test assignee email validation"""
        self.test_category.assign_issue_to_user = 1
        self.test_category.assignee = "invalid-email"
        
        with self.assertRaises(frappe.ValidationError):
            self.test_category.save()

    def test_valid_assignee_email(self):
        """Test valid assignee email"""
        self.test_category.assign_issue_to_user = 1
        self.test_category.assignee = "test@example.com"
        
        # Should not raise an error
        self.test_category.save()
        self.assertEqual(self.test_category.assignee, "test@example.com")

    def test_multiple_assignee_emails(self):
        """Test multiple assignee emails"""
        self.test_category.assign_issue_to_user = 1
        self.test_category.assignee = "test1@example.com, test2@example.com"
        
        # Should not raise an error
        self.test_category.save()
        self.assertEqual(self.test_category.assignee, "test1@example.com, test2@example.com")

    def test_escalation_validation(self):
        """Test escalation validation"""
        self.test_category.enable_escalation = 1
        # Missing escalation type should raise error
        with self.assertRaises(frappe.ValidationError):
            self.test_category.save()

    def test_escalation_with_type(self):
        """Test escalation with valid type"""
        self.test_category.enable_escalation = 1
        self.test_category.escalation_type = "Time-based"
        self.test_category.escalation_1_point = 24
        self.test_category.escalation_1_unit = "Hours"
        
        # Should not raise an error
        self.test_category.save()
        self.assertEqual(self.test_category.escalation_type, "Time-based")

    def test_invalid_escalation_point(self):
        """Test invalid escalation point"""
        self.test_category.enable_escalation = 1
        self.test_category.escalation_type = "Time-based"
        self.test_category.escalation_1_point = 0  # Invalid: must be > 0
        
        with self.assertRaises(frappe.ValidationError):
            self.test_category.save()

    def test_sub_categories(self):
        """Test adding sub categories"""
        # Add a sub category
        self.test_category.append("sub_categories", {
            "sub_category_name": "Test Sub Category",
            "sub_category_code": "TEST_SUB",
            "description": "Test sub category"
        })
        
        self.test_category.save()
        self.assertEqual(len(self.test_category.sub_categories), 1)
        self.assertEqual(self.test_category.sub_categories[0].sub_category_name, "Test Sub Category")

    def test_duplicate_sub_category_code(self):
        """Test duplicate sub category codes"""
        # Add first sub category
        self.test_category.append("sub_categories", {
            "sub_category_name": "Test Sub Category 1",
            "sub_category_code": "TEST_SUB",
            "description": "Test sub category 1"
        })
        
        # Add second sub category with same code
        self.test_category.append("sub_categories", {
            "sub_category_name": "Test Sub Category 2",
            "sub_category_code": "TEST_SUB",  # Same code
            "description": "Test sub category 2"
        })
        
        with self.assertRaises(frappe.ValidationError):
            self.test_category.save()

    def test_sub_category_email_validation(self):
        """Test sub category email validation"""
        # Add sub category with invalid email
        self.test_category.append("sub_categories", {
            "sub_category_name": "Test Sub Category",
            "sub_category_code": "TEST_SUB",
            "description": "Test sub category",
            "assign_issue_to_user": 1,
            "assignee": "invalid-email"
        })
        
        with self.assertRaises(frappe.ValidationError):
            self.test_category.save()

    def test_sub_category_escalation_validation(self):
        """Test sub category escalation validation"""
        # Add sub category with escalation enabled but no type
        self.test_category.append("sub_categories", {
            "sub_category_name": "Test Sub Category",
            "sub_category_code": "TEST_SUB",
            "description": "Test sub category",
            "enable_escalation": 1
            # Missing escalation_type
        })
        
        with self.assertRaises(frappe.ValidationError):
            self.test_category.save()

    def test_get_sub_categories_method(self):
        """Test get_sub_categories method"""
        # Add a sub category
        self.test_category.append("sub_categories", {
            "sub_category_name": "Test Sub Category",
            "sub_category_code": "TEST_SUB",
            "description": "Test sub category"
        })
        self.test_category.save()
        
        # Test the method
        sub_categories = self.test_category.get_sub_categories()
        self.assertEqual(len(sub_categories), 1)
        self.assertEqual(sub_categories[0]["sub_category_name"], "Test Sub Category")

    def test_get_assignment_info_method(self):
        """Test get_assignment_info method"""
        self.test_category.assign_issue_to_user = 1
        self.test_category.assignee = "test@example.com"
        self.test_category.assign_issue_to_external_vendor = 1
        self.test_category.save()
        
        assignment_info = self.test_category.get_assignment_info()
        self.assertEqual(assignment_info["assignee"], "test@example.com")
        self.assertTrue(assignment_info["assign_issue_to_user"])
        self.assertTrue(assignment_info["assign_issue_to_external_vendor"])

    def test_get_escalation_info_method(self):
        """Test get_escalation_info method"""
        self.test_category.enable_escalation = 1
        self.test_category.escalation_type = "Time-based"
        self.test_category.escalation_1_point = 24
        self.test_category.escalation_1_unit = "Hours"
        self.test_category.escalation_1_assignee = "escalation@example.com"
        self.test_category.save()
        
        escalation_info = self.test_category.get_escalation_info()
        self.assertEqual(escalation_info["escalation_type"], "Time-based")
        self.assertEqual(escalation_info["escalation_1"]["point"], 24)
        self.assertEqual(escalation_info["escalation_1"]["unit"], "Hours")
        self.assertEqual(escalation_info["escalation_1"]["assignee"], "escalation@example.com")

    def test_get_escalation_info_disabled(self):
        """Test get_escalation_info when escalation is disabled"""
        self.test_category.enable_escalation = 0
        self.test_category.save()
        
        escalation_info = self.test_category.get_escalation_info()
        self.assertEqual(escalation_info, {})


if __name__ == "__main__":
    unittest.main() 