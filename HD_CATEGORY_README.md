# HD Category Doctype Documentation

## Overview

The HD Category doctype is a comprehensive helpdesk category management system designed for PhysicsWallah's helpdesk requirements. It provides a hierarchical structure with categories and sub-categories, along with extensive configuration options for assignment rules, escalation settings, and form attachments.

## Doctype Structure

### HD Category (Main Doctype)
- **Location**: `apps/pw_helpdesk/pw_helpdesk/pw_helpdesk/doctype/hd_category/`
- **Purpose**: Manages helpdesk categories with assignment and escalation rules

### HD Sub Category (Child Table)
- **Location**: Embedded within HD Category as a child table
- **Purpose**: Manages sub-categories within main categories

## Key Features

### 1. Basic Information
- **Category Name**: Human-readable category name
- **Category Code**: Unique identifier for the category
- **Description**: Detailed description of the category
- **Is Active**: Toggle to enable/disable the category

### 2. Assignment Settings
- **Same Assignee as Category**: Inherit assignee from parent category
- **Assign Issue To User**: Enable direct user assignment
- **Assignee**: Email addresses of assigned users (comma-separated)
- **Assign Issue to External Vendor**: Enable external vendor assignment
- **Assign Issue to Permission Role Holder**: Enable role-based assignment
- **Permission Role Holder**: Specific role for assignment

### 3. Form Settings
- **Attach Form for Issue Creation**: Enable form attachment
- **Attach Same Form as Category**: Inherit form from parent category
- **Make Attachment Mandatory**: Require attachments for tickets
- **Same Attachment Setting as Category**: Inherit attachment settings
- **Hide Attachment Field**: Hide attachment field in forms
- **Display Sub-Category only in Mobile App**: Mobile-specific display
- **Make Location Mandatory**: Require location information

### 4. Escalation Settings
- **Same Escalation Settings as Category**: Inherit escalation from parent
- **Enable Escalation**: Enable escalation rules
- **Escalation Type**: Time-based, Status-based, or Priority-based
- **Three Escalation Levels**: Each with point, unit, and assignee

### 5. Sub Categories
- **Table Field**: Contains child HD Sub Category records
- **Hierarchical Structure**: Categories can have multiple sub-categories

## File Structure

```
apps/pw_helpdesk/pw_helpdesk/pw_helpdesk/doctype/
└── hd_category/
    ├── __init__.py
    ├── hd_category.json (includes HD Sub Category as child table)
    ├── hd_category.py (includes sub-category validation logic)
    ├── hd_category.js (includes sub-category UI logic)
    └── test_hd_category.py (includes sub-category tests)
```

## Installation and Setup

### 1. Install the Doctype
```bash
# Navigate to your Frappe bench
cd /path/to/your/bench

# Install the pw_helpdesk app
bench --site your-site.com install-app pw_helpdesk

# Migrate the database
bench --site your-site.com migrate
```

### 2. Import Sample Data
```bash
# Use the sample CSV file for initial data import
bench --site your-site.com import-csv apps/pw_helpdesk/sample_hd_category_import.csv HD Category
```

### 3. Create Categories via UI
1. Go to Desk > PW Helpdesk > HD Category
2. Click "New" to create a new category
3. Fill in the required fields
4. Add sub-categories in the "Sub Categories" table
5. Configure assignment and escalation settings
6. Save the document

## Usage Examples

### Creating a Category with Assignment Rules
```python
import frappe

# Create a new category
category = frappe.get_doc({
    "doctype": "HD Category",
    "category_name": "IT Support",
    "category_code": "IT_SUP",
    "description": "IT support related queries",
    "is_active": 1,
    "assign_issue_to_user": 1,
    "assignee": "it.support@company.com, tech.team@company.com"
})

category.insert()
```

### Adding Sub Categories
```python
# Add sub categories to the main category
category.append("sub_categories", {
    "sub_category_name": "Hardware Issues",
    "sub_category_code": "HW_ISSUE",
    "description": "Hardware related problems"
})

category.append("sub_categories", {
    "sub_category_name": "Software Issues",
    "sub_category_code": "SW_ISSUE",
    "description": "Software related problems"
})

category.save()
```

### Setting Up Escalation Rules
```python
# Configure escalation settings
category.enable_escalation = 1
category.escalation_type = "Time-based"
category.escalation_1_point = 24
category.escalation_1_unit = "Hours"
category.escalation_1_assignee = "escalation@company.com"
category.escalation_2_point = 48
category.escalation_2_unit = "Hours"
category.escalation_2_assignee = "manager@company.com"

category.save()
```

## Integration with HD Ticket

The HD Category doctype integrates with the existing HD Ticket system:

### 1. Custom Fields
- Add category and sub-category fields to HD Ticket
- Link tickets to specific categories and sub-categories

### 2. Assignment Rules
- Use category assignment settings to auto-assign tickets
- Implement role-based assignment based on category settings

### 3. Escalation Rules
- Create automatic escalation based on category settings
- Integrate with existing HD Escalation Rule system

### 4. Form Templates
- Use category form settings to customize ticket creation forms
- Implement dynamic form fields based on category configuration

## API Methods

### HD Category Methods
- `get_sub_categories()`: Returns all sub-categories for the category
- `get_assignment_info()`: Returns assignment configuration
- `get_escalation_info()`: Returns escalation configuration

### Sub Category Methods (within HD Category)
- Sub-categories are managed as child table records within HD Category
- All validation and business logic is handled through the parent HD Category

## Validation Rules

### HD Category Validation
- Category code must be unique
- Valid email addresses for assignees
- Escalation type required when escalation is enabled
- Escalation points must be greater than 0

### Sub Category Validation (within HD Category)
- Sub-category code must be unique within the parent category
- Valid email addresses for assignees
- Escalation type required when escalation is enabled
- Escalation points must be greater than 0

## Testing

Run the test suite to verify functionality:

```bash
# Run HD Category tests
bench --site your-site.com run-tests --module pw_helpdesk.pw_helpdesk.pw_helpdesk.doctype.hd_category.test_hd_category

# Run HD Category tests (includes sub-category tests)
bench --site your-site.com run-tests --module pw_helpdesk.pw_helpdesk.pw_helpdesk.doctype.hd_category.test_hd_category
```

## Customization

### Adding New Fields
1. Edit the respective `.json` file
2. Add field definitions to the `fields` array
3. Update the `field_order` array
4. Add validation logic in the `.py` file
5. Add UI logic in the `.js` file

### Extending Functionality
1. Add new methods to the Python classes
2. Create new API endpoints if needed
3. Extend the JavaScript functionality
4. Update tests to cover new features

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure CSV column names match doctype field names
2. **Validation Errors**: Check email format and required fields
3. **Permission Issues**: Verify user has appropriate permissions
4. **Database Errors**: Run migrations and check database integrity

### Debug Mode
Enable debug mode for detailed error messages:
```python
import frappe
frappe.flags.debug = True
```

## Support

For issues and questions:
1. Check the test files for usage examples
2. Review the validation logic in the Python files
3. Examine the JavaScript files for UI behavior
4. Consult the Frappe documentation for general doctype development

## Future Enhancements

Potential improvements for the HD Category system:
1. **Workflow Integration**: Add workflow support for category-based processes
2. **Analytics**: Add reporting and analytics based on categories
3. **API Integration**: Create REST API endpoints for external integrations
4. **Bulk Operations**: Add bulk import/export functionality
5. **Advanced Escalation**: Implement more sophisticated escalation rules
6. **Mobile App**: Enhance mobile app integration with category settings 