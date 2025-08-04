app_name = "pw_helpdesk"
app_title = "Pw Helpdesk"
app_publisher = "Hybrowlabs"
app_description = "helpdesk customization for PW"
app_email = "dhairya@mail.hybrowlabs.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "pw_helpdesk",
# 		"logo": "/assets/pw_helpdesk/logo.png",
# 		"title": "Pw Helpdesk",
# 		"route": "/pw_helpdesk",
# 		"has_permission": "pw_helpdesk.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pw_helpdesk/css/pw_helpdesk.css"
# app_include_js = "/assets/pw_helpdesk/js/pw_helpdesk.js"

# include js, css files in header of web template
# web_include_css = "/assets/pw_helpdesk/css/pw_helpdesk.css"
# web_include_js = "/assets/pw_helpdesk/js/pw_helpdesk.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pw_helpdesk/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"HD Service Level Agreement": "pw_helpdesk/custom/client_scripts/hd_service_level_agreement.js",
	"Assignment Rule": "pw_helpdesk/custom/client_scripts/assignment_rule.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "pw_helpdesk/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "pw_helpdesk.utils.jinja_methods",
# 	"filters": "pw_helpdesk.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "pw_helpdesk.install.before_install"
# after_install = "pw_helpdesk.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pw_helpdesk.uninstall.before_uninstall"
# after_uninstall = "pw_helpdesk.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pw_helpdesk.utils.before_app_install"
# after_app_install = "pw_helpdesk.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pw_helpdesk.utils.before_app_uninstall"
# after_app_uninstall = "pw_helpdesk.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pw_helpdesk.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"HD Ticket": {
		"validate": [
			"pw_helpdesk.customizations.ticket_events.validate_ticket_closure"
		],
		"after_insert": [
			"pw_helpdesk.customizations.ticket_events.auto_assign_agents_after_save",
			"pw_helpdesk.customizations.real_time_automation.ticket_enhanced_assignment"
		],
		"after_save": [
			"pw_helpdesk.customizations.ticket_events.auto_assign_agents_after_save",
			"pw_helpdesk.customizations.real_time_automation.ticket_enhanced_assignment"
		]
	},
	"HD Ticket Comment": {
		"after_insert": "pw_helpdesk.customizations.ticket_events.on_ticket_comment_insert"
	},
	"HD Team": {
		"validate": "pw_helpdesk.customizations.real_time_automation.team_real_time_sync",
		"after_save": [
			"pw_helpdesk.customizations.ticket_events.on_team_save",
			"pw_helpdesk.customizations.real_time_automation.team_real_time_sync"
		]
	},
	"HD Service Level Agreement": {
		"validate": "pw_helpdesk.customizations.real_time_automation.sla_real_time_validation"
	},
	"Assignment Rule": {
		"validate": "pw_helpdesk.customizations.real_time_automation.assignment_rule_real_time_validation"
	}
}

# Import enhanced SLA system
def after_install():
	"""Initialize enhanced SLA system after app installation"""
	try:
		import pw_helpdesk.customizations.enhanced_sla
	except ImportError:
		pass

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pw_helpdesk.tasks.all"
# 	],
# 	"daily": [
# 		"pw_helpdesk.tasks.daily"
# 	],
# 	"hourly": [
# 		"pw_helpdesk.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pw_helpdesk.tasks.weekly"
# 	],
# 	"monthly": [
# 		"pw_helpdesk.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "pw_helpdesk.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pw_helpdesk.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pw_helpdesk.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["pw_helpdesk.utils.before_request"]
# after_request = ["pw_helpdesk.utils.after_request"]

# Job Events
# ----------
# before_job = ["pw_helpdesk.utils.before_job"]
# after_job = ["pw_helpdesk.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"pw_helpdesk.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
fixtures = [
    {"dt": "HD Service Level Agreement", "dt":"HD Ticket"},
]

# Import enhanced SLA system on startup
def after_app_install():
	"""Initialize enhanced SLA system after app installation"""
	try:
		import pw_helpdesk.customizations.enhanced_sla
	except ImportError:
		pass
