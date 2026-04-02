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

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.phone = getattr(rec.partner_id, "phone", False) or ""
                rec.mobile = getattr(rec.partner_id, "mobile", False) or ""
                rec.email = getattr(rec.partner_id, "email", False) or ""