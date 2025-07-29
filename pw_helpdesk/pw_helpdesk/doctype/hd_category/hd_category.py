import frappe
from frappe.model.document import Document
from frappe import _


class HDCategory(Document):
    def validate(self):
        """Validate the HD Category document"""
        self.validate_category_code()
        self.validate_assignee_emails()
        self.validate_escalation_settings()
        self.validate_sub_category_settings()

    def validate_category_code(self):
        """Validate that category code is unique and follows naming convention"""
        if self.category_code:
            # Check if category code already exists
            existing = frappe.get_all(
                "HD Category",
                filters={"category_code": self.category_code, "name": ["!=", self.name]},
                limit=1
            )
            if existing:
                frappe.throw(_("Category Code '{0}' already exists").format(self.category_code))

    def validate_assignee_emails(self):
        """Validate assignee email addresses"""
        if self.assignee:
            emails = [email.strip() for email in self.assignee.split(",")]
            for email in emails:
                if email and not frappe.utils.validate_email_address(email):
                    frappe.throw(_("Invalid email address: {0}").format(email))

    def validate_escalation_settings(self):
        """Validate escalation settings"""
        if self.enable_escalation:
            if not self.escalation_type:
                frappe.throw(_("Escalation Type is required when escalation is enabled"))
            
            # Validate escalation levels
            if self.escalation_1_point and self.escalation_1_point <= 0:
                frappe.throw(_("Escalation 1 Point must be greater than 0"))
            
            if self.escalation_2_point and self.escalation_2_point <= 0:
                frappe.throw(_("Escalation 2 Point must be greater than 0"))
            
            if self.escalation_3_point and self.escalation_3_point <= 0:
                frappe.throw(_("Escalation 3 Point must be greater than 0"))

    def validate_sub_category_settings(self):
        """Validate sub category settings"""
        if self.is_sub_category:
            if not self.parent_category:
                frappe.throw(_("Parent Category is required when 'Is Sub Category' is checked"))
            
            # Check if parent category exists and is not a sub-category itself
            parent_doc = frappe.get_doc("HD Category", self.parent_category)
            if parent_doc.is_sub_category:
                frappe.throw(_("Parent Category cannot be a sub-category itself"))
        else:
            # If not a sub-category, parent_category should be empty
            if self.parent_category:
                frappe.throw(_("Parent Category should not be set for main categories"))

    def on_update(self):
        """Actions to perform when document is updated"""
        self.update_related_tickets()
        self.update_escalation_rules()

    def update_related_tickets(self):
        """Update related tickets if category settings change"""
        # This would update tickets that use this category
        pass

    def update_escalation_rules(self):
        """Update or create escalation rules based on category settings"""
        if self.enable_escalation:
            self.create_or_update_escalation_rule()

    def create_or_update_escalation_rule(self):
        """Create or update escalation rule for this category"""
        rule_name = f"Escalation Rule - {self.category_name}"
        
        # Check if escalation rule exists
        existing_rule = frappe.get_all(
            "HD Escalation Rule",
            filters={"name": rule_name},
            limit=1
        )
        
        if existing_rule:
            # Update existing rule
            rule = frappe.get_doc("HD Escalation Rule", rule_name)
        else:
            # Create new rule
            rule = frappe.get_doc({
                "doctype": "HD Escalation Rule",
                "name": rule_name,
                "is_enabled": 1
            })
        
        # Update rule settings based on category escalation settings
        # This is a simplified implementation
        rule.save()

    @frappe.whitelist()
    def get_sub_categories(self):
        """Get all sub categories for this category"""
        sub_categories = frappe.get_all(
            "HD Category",
            filters={"parent_category": self.name, "is_sub_category": 1, "is_active": 1},
            fields=["category_name", "category_code", "description", "assignee", "enable_escalation"]
        )
        return sub_categories

    @frappe.whitelist()
    def get_assignment_info(self):
        """Get assignment information for this category"""
        info = {
            "category": {
                "assignee": self.assignee,
                "assign_issue_to_user": self.assign_issue_to_user,
                "assign_issue_to_external_vendor": self.assign_issue_to_external_vendor,
                "assign_issue_to_permission_role_holder": self.assign_issue_to_permission_role_holder,
                "permission_role_holder": self.permission_role_holder
            },
            "sub_categories": []
        }
        
        # Get sub-categories assignment info
        sub_categories = frappe.get_all(
            "HD Category",
            filters={"parent_category": self.name, "is_sub_category": 1, "is_active": 1},
            fields=["category_name", "category_code", "assignee", "assign_issue_to_user", 
                   "assign_issue_to_external_vendor", "assign_issue_to_permission_role_holder", "permission_role_holder"]
        )
        
        info["sub_categories"] = sub_categories
        return info

    @frappe.whitelist()
    def get_escalation_info(self):
        """Get escalation information for this category"""
        info = {
            "category_escalation": {
                "enabled": self.enable_escalation,
                "type": self.escalation_type,
                "levels": []
            },
            "sub_categories": []
        }
        
        if self.enable_escalation:
            info["category_escalation"]["levels"] = [
                {
                    "level": 1,
                    "point": self.escalation_1_point,
                    "unit": self.escalation_1_unit,
                    "assignee": self.escalation_1_assignee
                },
                {
                    "level": 2,
                    "point": self.escalation_2_point,
                    "unit": self.escalation_2_unit,
                    "assignee": self.escalation_2_assignee
                },
                {
                    "level": 3,
                    "point": self.escalation_3_point,
                    "unit": self.escalation_3_unit,
                    "assignee": self.escalation_3_assignee
                }
            ]
        
        # Get sub-categories escalation info
        sub_categories = frappe.get_all(
            "HD Category",
            filters={"parent_category": self.name, "is_sub_category": 1, "is_active": 1},
            fields=["category_name", "category_code", "enable_escalation", "escalation_type",
                   "escalation_1_point", "escalation_1_unit", "escalation_1_assignee",
                   "escalation_2_point", "escalation_2_unit", "escalation_2_assignee",
                   "escalation_3_point", "escalation_3_unit", "escalation_3_assignee"]
        )
        
        for sub_cat in sub_categories:
            sub_info = {
                "name": sub_cat.category_name,
                "code": sub_cat.category_code,
                "escalation": {
                    "enabled": sub_cat.enable_escalation,
                    "type": sub_cat.escalation_type,
                    "levels": []
                }
            }
            
            if sub_cat.enable_escalation:
                sub_info["escalation"]["levels"] = [
                    {
                        "level": 1,
                        "point": sub_cat.escalation_1_point,
                        "unit": sub_cat.escalation_1_unit,
                        "assignee": sub_cat.escalation_1_assignee
                    },
                    {
                        "level": 2,
                        "point": sub_cat.escalation_2_point,
                        "unit": sub_cat.escalation_2_unit,
                        "assignee": sub_cat.escalation_2_assignee
                    },
                    {
                        "level": 3,
                        "point": sub_cat.escalation_3_point,
                        "unit": sub_cat.escalation_3_unit,
                        "assignee": sub_cat.escalation_3_assignee
                    }
                ]
            
            info["sub_categories"].append(sub_info)
        
        return info 