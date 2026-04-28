from odoo import fields, models


class WaMarketingChurnSignal(models.Model):
    _name = "wa.marketing.churn.signal"
    _description = "WA Marketing Churn Signal"
    _order = "created_at desc, id desc"

    customer_profile_id = fields.Many2one(
        "wa.marketing.customer.profile",
        string="Customer Profile",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        ondelete="set null",
        index=True,
    )

    phone = fields.Char(string="Phone", index=True)
    signal_type = fields.Selection(
        [
            ("rule_based_churn", "Rule Based Churn"),
            ("inactivity", "Inactivity"),
            ("missed_routine", "Missed Routine"),
            ("basket_drop", "Basket Drop"),
            ("frequency_drop", "Frequency Drop"),
        ],
        string="Signal Type",
        required=True,
        default="rule_based_churn",
    )
    score = fields.Float(string="Score", digits=(16, 2), default=0.0)
    risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Risk Level",
        default="low",
        required=True,
    )
    reason = fields.Text(string="Reason")

    expected_next_order_at = fields.Datetime(string="Expected Next Order At")
    actual_last_order_at = fields.Datetime(string="Actual Last Order At")

    is_active = fields.Boolean(string="Active", default=True)
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now, readonly=True)