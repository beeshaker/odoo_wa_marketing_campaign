from odoo import api, fields, models


class WaMarketingCustomerProfile(models.Model):
    _name = "wa.marketing.customer.profile"
    _description = "WA Marketing Customer Profile"
    _order = "churn_risk_score desc, id desc"
    _rec_name = "display_name"

    active = fields.Boolean(default=True)

    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        ondelete="set null",
        index=True,
    )
    display_name = fields.Char(
        string="Name",
        compute="_compute_display_name",
        store=True,
    )

    phone = fields.Char(string="Phone", index=True)
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")

    total_orders = fields.Integer(string="Total Orders", default=0)
    avg_order_value = fields.Float(string="Avg Order Value", digits=(16, 2), default=0.0)
    avg_days_between_orders = fields.Float(string="Avg Days Between Orders", digits=(16, 2), default=0.0)

    preferred_day_of_week = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Preferred Day",
    )
    preferred_hour = fields.Integer(string="Preferred Hour")
    favorite_item = fields.Char(string="Favorite Item")

    last_order_at = fields.Datetime(string="Last Order At")
    expected_next_order_at = fields.Datetime(string="Expected Next Order At")

    churn_risk_score = fields.Float(string="Churn Risk Score", digits=(16, 2), default=0.0)
    churn_risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Churn Risk Level",
        default="low",
    )
    churn_reason = fields.Text(string="Churn Reason")
    last_profile_refresh_at = fields.Datetime(string="Last Profile Refresh")

    churn_signal_ids = fields.One2many(
        "wa.marketing.churn.signal",
        "customer_profile_id",
        string="Churn Signals",
    )

    @api.depends("partner_id", "phone", "mobile", "email")
    def _compute_display_name(self):
        for rec in self:
            if rec.partner_id:
                rec.display_name = rec.partner_id.display_name
            elif rec.phone:
                rec.display_name = rec.phone
            elif rec.mobile:
                rec.display_name = rec.mobile
            elif rec.email:
                rec.display_name = rec.email
            else:
                rec.display_name = "Customer Profile"