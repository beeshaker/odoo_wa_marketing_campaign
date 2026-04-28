from odoo import api, fields, models


class WaMarketingCampaignRecipient(models.Model):
    _name = "wa.marketing.campaign.recipient"
    _description = "WhatsApp Marketing Campaign Recipient"
    _order = "id desc"

    campaign_id = fields.Many2one(
        "wa.marketing.campaign",
        required=True,
        ondelete="cascade",
    )

    partner_id = fields.Many2one("res.partner", string="Contact")

    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")

    send_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("queued", "Queued"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("failed", "Failed"),
            ("excluded", "Excluded"),
        ],
        default="pending",
    )
    external_message_id = fields.Char()
    failure_reason = fields.Char()
    opted_in = fields.Boolean(default=True)

    customer_profile_id = fields.Many2one(
        "wa.marketing.customer.profile",
        string="Customer Profile",
        compute="_compute_customer_profile_id",
        store=False,
    )
    churn_risk_score = fields.Float(
        string="Churn Risk Score",
        compute="_compute_customer_profile_fields",
        store=False,
    )
    churn_risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Churn Risk Level",
        compute="_compute_customer_profile_fields",
        store=False,
    )
    churn_reason = fields.Text(
        string="Churn Reason",
        compute="_compute_customer_profile_fields",
        store=False,
    )
    favorite_item = fields.Char(
        string="Favorite Item",
        compute="_compute_customer_profile_fields",
        store=False,
    )
    last_order_at = fields.Datetime(
        string="Last Order At",
        compute="_compute_customer_profile_fields",
        store=False,
    )
    expected_next_order_at = fields.Datetime(
        string="Expected Next Order At",
        compute="_compute_customer_profile_fields",
        store=False,
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.phone = getattr(rec.partner_id, "phone", False) or ""
                rec.mobile = getattr(rec.partner_id, "mobile", False) or ""
                rec.email = getattr(rec.partner_id, "email", False) or ""

    @api.depends("partner_id", "phone", "mobile", "email")
    def _compute_customer_profile_id(self):
        Profile = self.env["wa.marketing.customer.profile"]
        for rec in self:
            profile = False
            if rec.partner_id:
                profile = Profile.search([("partner_id", "=", rec.partner_id.id)], limit=1)

            if not profile and rec.phone:
                profile = Profile.search([("phone", "=", rec.phone)], limit=1)

            if not profile and rec.mobile:
                profile = Profile.search([("mobile", "=", rec.mobile)], limit=1)

            if not profile and rec.email:
                profile = Profile.search([("email", "=", rec.email)], limit=1)

            rec.customer_profile_id = profile

    @api.depends("customer_profile_id")
    def _compute_customer_profile_fields(self):
        for rec in self:
            profile = rec.customer_profile_id
            rec.churn_risk_score = profile.churn_risk_score if profile else 0.0
            rec.churn_risk_level = profile.churn_risk_level if profile else False
            rec.churn_reason = profile.churn_reason if profile else False
            rec.favorite_item = profile.favorite_item if profile else False
            rec.last_order_at = profile.last_order_at if profile else False
            rec.expected_next_order_at = profile.expected_next_order_at if profile else False